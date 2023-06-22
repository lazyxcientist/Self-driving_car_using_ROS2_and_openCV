import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import ExecuteProcess


def generate_launch_description():

    package_dir = get_package_share_directory('drive')
    world_path = os.path.join(package_dir,'world','traffic.world')


    return LaunchDescription([

        ExecuteProcess(
        cmd=['gazebo','--verbose',world_path,'-s','libgazebo_ros_factory.so'],
        output='screen',
        )
        # Node(
        #     package='drive',
        #     executable='/* exec_name */',
        #     name='/* node_name */',
        #     output='screen'),
    ])
