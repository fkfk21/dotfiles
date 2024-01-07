if status is-interactive
  # use the 
  fish_config theme choose Tomorrow\ Night\ Bright
end


# alias colcon='__colcon_find_workspace_dir > /dev/null && cd (__colcon_find_workspace_dir); command colcon'
# alias roscd="ccd -o"

# add abbr
abbr -a gcom git commit -m 
abbr -a gst git status
abbr -a ga git add .
abbr -a fconf vim ~/.config/fish/config.fish
abbr -a bconf vim ~/.bashrc
abbr -a poetry-activate source '$(poetry env info --path)/bin/activate.fish'

# ros2 build command
if test -d ~/ros2_ws
  abbr -a ros2build "cd ~/ros2_ws && colcon build --symlink-install"
end
if test -d ~/rogy_ws
  abbr -a wsbuild "cd ~/rogy_ws && colcon build --symlink-install"
end

# asdf
if test -d ~/.asdf
  source ~/.asdf/asdf.fish
end

# python
set -x VIRTUAL_ENV_DISABLE_PROMPT 1

# settings for Isaac Sim
set -x ISAAC_SIM_VERSION 2022.2.1
if test -d ~/.local/share/ov/pkg
  set -x ISAACSIM_PATH $HOME/.local/share/ov/pkg/isaac_sim-$ISAAC_SIM_VERSION
  set -x ISAACSIM_PYTHON $ISAACSIM_PATH/python.sh
  alias isaacsim_python=$ISAACSIM_PATH/python.sh
end

# matlab path
#set matlabpath /usr/local/MATLAB/R2022a/bin
#if test -d $matlabpath
#  set -x PATH $matlabpath $PATH
#end

if [ "$ROS_VERSION" = "1" ]
    source /opt/ros/noetic/share/rosbash/rosfish
else if [ "$ROS_VERSION" = "2" ]
    register-python-argcomplete --shell fish ros2 | source
    register-python-argcomplete --shell fish colcon | source
end
