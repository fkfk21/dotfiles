if status is-interactive
  # use the 
  fish_config theme choose Tomorrow\ Night\ Bright
end


# alias colcon='__colcon_find_workspace_dir > /dev/null && cd (__colcon_find_workspace_dir); command colcon'
# alias roscd="ccd -o"

# add abbr
abbr -a gcom git commit -m 
abbr -a gst git status
abbr -a fconf vim ~/.config/fish/config.fish

# ros2 build command
if test -d ~/ros2_ws
  abbr -a ros2-build "cd ~/ros2_ws && colcon build"
end

# python
set -x VIRTUAL_ENV_DISABLE_PROMPT 1


if [ "$ROS_VERSION" = "1" ]
    source /opt/ros/noetic/share/rosbash/rosfish
else if [ "$ROS_VERSION" = "2" ]
    register-python-argcomplete --shell fish ros2 | source
    register-python-argcomplete --shell fish colcon | source
end
