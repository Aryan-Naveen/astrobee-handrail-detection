#!/usr/bin/env python3


import cv2
import numpy as np

assert float(cv2.__version__.rsplit('.', 1)[0]) >= 3, 'OpenCV version 3 or newer required.'

class Undistorter:
    def __init__(self, simulation = True):
        if simulation:
            self.K = np.array([[272.2921804722079,          0.      ,    160.0],
                          [        0.      , 272.2921804722079,    120.0],
                          [        0.      ,          0.      ,     1.  ]])
            dims = np.asarray((320, 240))
            dist = 1.06251
        else:
            self.K = np.array([[251.16995333333332,          0.      ,    188.45150666666666],
                          [        0.      , 251.16995333333332,    161.27091333333334],
                          [        0.      ,          0.      ,     1.  ]])
            dist = 1.00447

            # camera_dims = np.asarray((1280, 960))

            dims = np.asarray((320, 240))

            # self.K = self.K / (camera_dims/dims)[0]


        # FOV model -
        K_undist = self.K.copy()
        K_undist[0:2,2] = dims/2.
        #get set of x-y coordinates
        coords = np.mgrid[0:dims[0], 0:dims[1]].reshape((2, np.prod(dims)))
        #need to compute source coordinates on distorted image for undist image
        normalized_coords = np.linalg.solve(K_undist, np.vstack((coords, np.ones(coords.shape[1]))))

        #FOV model
        coeff1 = 1./dist
        coeff2 = 2 * np.tan(dist/2)
        rus = np.linalg.norm(normalized_coords[:2], axis=0)
        rds = np.arctan(rus * coeff2) * coeff1

        conv = np.ones(rus.shape)
        valid_pts = rus > 1e-5
        conv[valid_pts] = rds[valid_pts]/rus[valid_pts]

        scaled_coords = normalized_coords
        scaled_coords[0:2] *= conv
        dist_coords = np.matmul(self.K, scaled_coords)[:2, :].reshape((2, dims[0], dims[1]))
        self.dist_coords_ = np.transpose(dist_coords, axes=(0,2,1)).astype(np.float32)


    def undistort(self, img):
        undist_img = cv2.remap(img, self.dist_coords_[0], self.dist_coords_[1], cv2.INTER_CUBIC)
        return undist_img



if __name__=='__main__':
    undist = Undistorter()

    img = cv2.imread('dist.png')
    undistorted_img = undist.undistort(img)
    cv2.imshow('undistorted', undistorted_img)
    cv2.waitKey()
    cv2.imwrite('undist.png', undistorted_img)
