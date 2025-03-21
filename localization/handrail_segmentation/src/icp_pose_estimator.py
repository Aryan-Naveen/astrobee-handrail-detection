#!/usr/bin/env python3

from __future__ import division

import rospy
from rospkg import RosPack
from std_msgs.msg import UInt8, Int16MultiArray, MultiArrayDimension
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import Pose
import utils.icp

import open3d as o3d
import numpy as np
from utils.transformation import TransformAlignment
import utils.icp as icp
from utils.converter import *
import copy
from probreg import cpd
from scipy.spatial.transform import Rotation as R

import timeit
import tf2_ros

from handrail_segmentation.msg import EkfState
import geometry_msgs

def draw_registration_result(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.voxel_down_sample(voxel_size=0.1)
    source_temp.paint_uniform_color([1, 0.706, 0])
    target_temp.paint_uniform_color([0, 0.651, 0.929])
    source_temp.transform(transformation)
    # o3d.visualization.draw_geometries([source_temp, target_temp], point_show_normal=True)


def preprocess_point_cloud(pcd, voxel_size, radius, should_voxel=True):
    if should_voxel:
        pcd_down = pcd.voxel_down_sample(voxel_size)
    else:
        pcd_down = pcd
    radius_normal = radius * 2
    pcd_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))
    radius_feature = radius * 5
    pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100))
    return pcd_down, pcd_fpfh





def execute_global_registration(src, target, voxel_size=0.01):
    source_down = src.voxel_down_sample(voxel_size=voxel_size)
    target_down = target.voxel_down_sample(voxel_size=voxel_size)
    result, _, _= cpd.registration_cpd(source_down, target_down)

    return result, result.transform(src.points)


class DOFPoseEstimator():
    def __init__(self):
        self.handrail_p = None
        self.handrail_q = None
        self.br = tf2_ros.TransformBroadcaster()

        self.pointcloud_topic = rospy.get_param('~segmented_object_topic', '/hw/detected_handrail/points')
        self.pub_ = rospy.Publisher('/hw/detected_handrail/pose', Pose, queue_size=10)
        self.pub_non_transform = rospy.Publisher('/hw/detected_handrail/reference', PointCloud2, queue_size=10)
        self.pub_visualize = rospy.Publisher('/hw/detected_handrail/transform', PointCloud2, queue_size=10)

        # Define subscribers
        self.pointcloud_sub = rospy.Subscriber(self.pointcloud_topic, PointCloud2, self.pointcloud_callback, queue_size = 1, buff_size = 2**24)
        self.align_transformer = TransformAlignment()


    def pointcloud_callback(self, points_msg):
        start = timeit.default_timer()
        points_msg_world = self.align_transformer.dock_to_world_transform(points_msg)

        detected_handrail = self.align_transformer.convert_pc_msg_to_np(points_msg_world)
        detected_handrail_o3d = o3d.geometry.PointCloud()
        detected_handrail_o3d.points = o3d.utility.Vector3dVector(detected_handrail)

        registered_handrail_o3d = o3d.io.read_point_cloud('/home/anaveen/Documents/nasa_ws/astrobee-detection-pipeline/src/handrail_segmentation/src/reference_pointclouds/handrail_30.pcd')
        registered_handrail = np.asarray(registered_handrail_o3d.points)
        self.pub_non_transform.publish(convertPc2(registered_handrail, frame_id = "dock_cam"))

        rospy.loginfo("Running ICP to estimate 6 DOF pose of detected object")
        reg_p2p, visualize = execute_global_registration(registered_handrail_o3d, detected_handrail_o3d)
        quat = R.from_matrix(reg_p2p.rot).as_quat()

        handrail_pose_msg = Pose()
        handrail_pose_msg.position.x = reg_p2p.t[0]
        handrail_pose_msg.position.y = reg_p2p.t[1]
        handrail_pose_msg.position.z = reg_p2p.t[2]
        handrail_pose_msg.orientation.x = quat[0]
        handrail_pose_msg.orientation.y = quat[1]
        handrail_pose_msg.orientation.z = quat[2]
        handrail_pose_msg.orientation.w = quat[3]

        t = geometry_msgs.msg.TransformStamped()

        t.header.stamp = rospy.Time.now()
        t.header.frame_id = "dock_cam"
        t.child_frame_id = "handrail"
        t.transform.translation.x = reg_p2p.t[0]
        t.transform.translation.y = reg_p2p.t[1]
        t.transform.translation.z = reg_p2p.t[2]
        t.transform.rotation.x = quat[0]
        t.transform.rotation.y = quat[1]
        t.transform.rotation.z = quat[2]
        t.transform.rotation.w = quat[3]
        self.br.sendTransform(t)
        rospy.loginfo("Done")
        # handrail_pose_msg = self.align_transformer.transform_pose_estimate(handrail_pose_msg)

        self.pub_.publish(handrail_pose_msg)
        self.pub_visualize.publish(convertPc2(visualize, frame_id = "dock_cam"))
        stop = timeit.default_timer()

        rospy.loginfo("Done running ICP to estimate 6 DOF pose of detected object")
        rospy.loginfo("~~~~~~~~~~~~~Pointcloud Registration took " + str(stop - start) + " seconds.~~~~~~~~~~~~~~~~")

if __name__=="__main__":
    # Initialize node
    rospy.init_node("icp_pose_estimator_node")

    # Define detector object
    dm = DOFPoseEstimator()

    # Spin
    rospy.spin()
