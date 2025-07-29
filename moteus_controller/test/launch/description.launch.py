import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, LogInfo
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from launch_ros.parameter_descriptions import ParameterValue

from launch_ros.actions import Node

# ros2 launch moteus_controller gazebo_test.launch.py urdf_file:=single_joint_test.urdf.xacro 
# ros2 launch moteus_controller gazebo_test.launch.py urdf_file:=multiple_joints_test.urdf.xacro 
# ros2 launch moteus_controller gazebo_test.launch.py urdf_file:=chaining_joint_test.urdf.xacro activate_chain:=true
# ros2 launch moteus_controller gazebo_test.launch.py urdf_file:=pos_vel_chain_test.urdf.xacro activate_chain:=true

def generate_launch_description():

    LD = []

    LD.append(DeclareLaunchArgument("description_file", default_value="single_joint_test.urdf.xacro"))
    LD.append(DeclareLaunchArgument('rviz', default_value="true"))
    LD.append(DeclareLaunchArgument('jsp_gui', default_value="true"))

    urdf = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]), " ",
        PathJoinSubstitution([FindPackageShare("moteus_controller"), "test/urdf", LaunchConfiguration("description_file")]), " ",
        # "safety_limits:=", LaunchConfiguration("safety_limits"), " ",
    ])

    LD.append(DeclareLaunchArgument("robot_description", default_value=urdf))


    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[{"robot_description": urdf}, {"use_sim_time": True}],
    )
    LD.append(robot_state_pub_node)

    joint_state_publisher_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        condition=IfCondition(LaunchConfiguration("jsp_gui"))
    )
    LD.append(joint_state_publisher_node)

    rviz_config_file = PathJoinSubstitution([FindPackageShare("moteus_controller"), "test/config/default.rviz"])

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(LaunchConfiguration("rviz"))
    )
    LD.append(rviz_node)


    return LaunchDescription(LD)