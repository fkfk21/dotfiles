if status is-interactive
  # use the 
  # fish_config theme choose Tomorrow\ Night\ Bright
  set -U fish_color_normal normal
  set -U fish_color_command c397d8
  set -U fish_color_quote b9ca4a
  set -U fish_color_redirection 70c0b1
  set -U fish_color_end c397d8
  set -U fish_color_error d54e53
  set -U fish_color_param 7aa6da
  set -U fish_color_comment e7c547
  set -U fish_color_match --background=brblue
  set -U fish_color_selection white --bold --background=brblack
  set -U fish_color_search_match bryellow --background=brblack
  set -U fish_color_history_current --bold
  set -U fish_color_operator 00a6b2
  set -U fish_color_escape 00a6b2
  set -U fish_color_cwd green
  set -U fish_color_cwd_root red
  set -U fish_color_valid_path --underline
  set -U fish_color_autosuggestion 969896
  set -U fish_color_user brgreen
  set -U fish_color_host normal
  set -U fish_color_cancel -r
  set -U fish_pager_color_completion normal
  set -U fish_pager_color_description B3A06D yellow
  set -U fish_pager_color_prefix normal --bold --underline
  set -U fish_pager_color_progress brwhite --background=cyan
end


# alias colcon='__colcon_find_workspace_dir > /dev/null && cd (__colcon_find_workspace_dir); command colcon'
# alias roscd="ccd -o"
alias cless='ccze -A | less -R'

# add abbr
abbr -a gcom git commit -m 
abbr -a gst git status
abbr -a ga git add .
abbr -a fconf vim ~/.config/fish/config.fish
abbr -a bconf vim ~/.bashrc
abbr -a pa source '(poetry env info --path)/bin/activate.fish'
abbr -a poetry-activate source '(poetry env info --path)/bin/activate.fish'
abbr -a apt-upg "sudo apt list --upgradable | grep keyword | awk -F/ '{print \$1}' | xargs sudo apt install -y"
abbr -a pcd cd '(dirname $VIRTUAL_ENV)'

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

# zoxide (command zi)
if type zoxide > /dev/null 2>&1
  zoxide init fish | source
end


# python
set -x VIRTUAL_ENV_DISABLE_PROMPT 1

# settings for Isaac Sim
set -x ISAAC_SIM_VERSION isaac-sim-4.0.0
if test -d ~/.local/share/ov/pkg
  set -x ISAACSIM_PATH $HOME/.local/share/ov/pkg/$ISAAC_SIM_VERSION
  set -x ISAACSIM_PYTHON $ISAACSIM_PATH/python.sh
  alias iscpy=$ISAACSIM_PATH/python.sh
  abbr -a cisc cd $ISAACSIM_PATH
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
