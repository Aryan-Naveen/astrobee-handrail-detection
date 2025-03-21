/*
 * Copyright (C) 2020 Open Source Robotics Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
*/
#ifndef SYSTEM_PLUGIN_DataGeneration_HH_
#define SYSTEM_PLUGIN_DataGeneration_HH_

#include <chrono>
#include <ignition/gazebo/System.hh>
#include <thread>
#include <vector>
#include <ignition/gazebo/SdfEntityCreator.hh>

namespace data_generation
{

  /// \brief Example showing different ways of commanding an actor.
  class DataGeneration:
    public ignition::gazebo::System,
    public ignition::gazebo::ISystemConfigure,
    public ignition::gazebo::ISystemPreUpdate
  {
    /// \brief Constructor
    public: DataGeneration();

    /// \brief Destructor
    public: ~DataGeneration() override;

    /// Documentation inherited
    public: void Configure(const ignition::gazebo::Entity &_id,
                           const std::shared_ptr<const sdf::Element> &_sdf,
                           ignition::gazebo::EntityComponentManager &_ecm,
                           ignition::gazebo::EventManager &_eventMgr) final;

    // Documentation inherited
    public: void PreUpdate(const ignition::gazebo::UpdateInfo &_info,
                ignition::gazebo::EntityComponentManager &_ecm) override;

    /// \brief Actor entity
    private: ignition::gazebo::Entity entity;
    private: ignition::gazebo::EntityComponentManager ecm;
    private: ignition::gazebo::EventManager eventMgr;
    private: ignition::gazebo::SdfEntityCreator entityCreator = ignition::gazebo::SdfEntityCreator(ecm, eventMgr);

    private: int lastPositionChange{0};

    private: std::vector<ignition::math::Pose3d> handrailInspectPositions;

    private: int NUM_IMAGES_EACH = 250;

    private: int n_count = 0;




  };
}

#endif
