if status is-interactive
  # use the 
  fish_config theme choose Tomorrow\ Night\ Bright
end


# alias colcon='__colcon_find_workspace_dir > /dev/null && cd (__colcon_find_workspace_dir); command colcon'
# alias roscd="ccd -o"

if [ "$ROS_VERSION" = "1" ]
    source /opt/ros/noetic/share/rosbash/rosfish
else if [ "$ROS_VERSION" = "2" ]
    register-python-argcomplete --shell fish ros2 | source
end
