import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'fast_lio'
    
    # Arguments
    map_path_arg = DeclareLaunchArgument(
        'map_path',
        default_value=os.path.join(
            get_package_share_directory(package_name), 
            'PCD', 
            'mine_map3_final_clean.pcd'
        ),
        description='Path to the global PCD map file'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (bag) time if true'
    )

    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value='velodyne_vlp16.yaml',
        description='FAST-LIO config file name (must be in config folder)'
    )

    # PMF Parameters
    use_pmf_arg = DeclareLaunchArgument(
        'use_pmf',
        default_value='true',
        description='Use PMF for ground segmentation'
    )
    pmf_max_window_size_arg = DeclareLaunchArgument(
        'pmf_max_window_size',
        default_value='5.0',
        description='PMF max window size'
    )
    pmf_slope_arg = DeclareLaunchArgument(
        'pmf_slope',
        default_value='1.0',
        description='PMF slope'
    )
    pmf_initial_distance_arg = DeclareLaunchArgument(
        'pmf_initial_distance',
        default_value='0.8',
        description='PMF initial distance'
    )
    pmf_max_distance_arg = DeclareLaunchArgument(
        'pmf_max_distance',
        default_value='1.0',
        description='PMF max distance'
    )

    # 1. Global Map Server
    map_server_node = Node(
        package=package_name,
        executable='global_map_server',
        name='global_map_server',
        output='screen',
        parameters=[{
            'map_path': LaunchConfiguration('map_path'),
            'map_frame_id': 'map',
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'use_pmf': LaunchConfiguration('use_pmf'),
            'pmf_max_window_size': LaunchConfiguration('pmf_max_window_size'),
            'pmf_slope': LaunchConfiguration('pmf_slope'),
            'pmf_initial_distance': LaunchConfiguration('pmf_initial_distance'),
            'pmf_max_distance': LaunchConfiguration('pmf_max_distance'),
        }]
    )

    # 2. FAST-LIO (Odometry Mode)
    # We load the YAML file but override specific params for localization mode
    fast_lio_config_path = PathJoinSubstitution([
        get_package_share_directory(package_name),
        'config',
        LaunchConfiguration('config_file')
    ])

    fast_lio_node = Node(
        package=package_name,
        executable='fastlio_mapping',
        name='fastlio_mapping',
        output='screen',
        parameters=[
            fast_lio_config_path,
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                # Overrides for Localization Mode
                'publish.map_en': False,
                'pcd_save.pcd_save_en': False,
                'mapping.extrinsic_est_en': False,
                'publish.scan_publish_en': True,
                'publish.scan_bodyframe_pub_en': True,
                'publish.dense_publish_en': False,
            }
        ]
    )

    # 3. Localization Node (NDT)
    localization_node = Node(
        package=package_name,
        executable='localization_node',
        name='localization_node',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'global_frame_id': 'map',
            'odom_frame_id': 'camera_init',
            'base_frame_id': 'base_link',
            'ndt_resolution': 1.0,
            'ndt_step_size': 0.1,
            'ndt_max_iter': 30
        }]
    )

    # RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', PathJoinSubstitution([get_package_share_directory(package_name), 'rviz', 'localization.rviz'])],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    return LaunchDescription([
        map_path_arg,
        use_sim_time_arg,
        config_file_arg,
        use_pmf_arg,
        pmf_max_window_size_arg,
        pmf_slope_arg,
        pmf_initial_distance_arg,
        pmf_max_distance_arg,
        map_server_node,
        fast_lio_node,
        localization_node,
        rviz_node
    ])
