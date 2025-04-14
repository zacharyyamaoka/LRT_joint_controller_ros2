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

    declared_arguments = []

    declared_arguments.append(DeclareLaunchArgument("urdf_file", default_value="single_joint_test.urdf.xacro"))
    declared_arguments.append(DeclareLaunchArgument("activate_chain",default_value="false"))

    # Get URDF via xacro
    robot_description_content = ParameterValue(
        Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("moteus_controller"),
                    "urdf",
                    LaunchConfiguration("urdf_file"),
                ]
            ),
        ]
    ), value_type=str)

    # Set up dictionary parameters:
    robot_description = {"robot_description": robot_description_content}
    use_sim_time = {"use_sim_time": True}

    # Load world for gazebo sim
    world = PathJoinSubstitution(
        [
            FindPackageShare("moteus_controller"),
            "worlds",
            'empty.sdf'
        ]
    )

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, use_sim_time],
    )

    spawn_entity = Node(package='ros_gz_sim', executable='create',
                    arguments=['-topic', 'robot_description',
                                '-name', 'Meldog'],
                    output='screen')

    load_joint_state_broadcaster = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'joint_state_broadcaster'],
        output='screen'
    )

    load_moteus_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'moteus_controller'],
        output='screen'
    )

    load_higher_level_controller =  ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'higher_level_controller'],
        output='screen',
        condition=IfCondition(LaunchConfiguration("activate_chain")),
    )


    gazebo_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch'), '/gz_sim.launch.py']),
            launch_arguments={'gz_args': ['-r -v1 ', world], 'on_exit_shutdown': 'true'}.items()
        )
    
    gazebo_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )


    nodes = [
        gazebo_sim,
        gazebo_bridge,
        LogInfo(msg=["Using world file: ", world]),

        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[load_joint_state_broadcaster],
            )
        ),

        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action= load_joint_state_broadcaster,
                on_exit=[load_moteus_controller],
            )
        ),

        # Without this delay, it doesn't load properly. Higher level comes after lower level
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action= load_moteus_controller,
                on_exit=[load_higher_level_controller],
            )
        ),

        robot_state_pub_node,
        spawn_entity,
    ]

    # Once gazebo is running, get current view with: 
    # gz topic -e -t /gui/camera/pose
    # then update string below
    set_camera_pose = ExecuteProcess(
        cmd=[
            "gz", "service",
            "-s", "/gui/move_to/pose",
            "--reqtype", "gz.msgs.GUICamera",
            "--reptype", "gz.msgs.Boolean",
            "--timeout", "10000",
            "--req",
            "pose: { position: { x: 2.8076, y: -0.0203, z: 1.1676 }, "
            "orientation: { x: 0.1676, y: 0.0012, z: -0.9858, w: 0.0072 } }"
        ],
        shell=False,
        output="screen"
    )
    declared_arguments.append(set_camera_pose)

    return LaunchDescription(declared_arguments + nodes)