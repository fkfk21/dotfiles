# ~/.bashrc: executed by bash(1) for non-login shells.

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# original .bashrc
source /etc/skel/.bashrc

# Add user's private bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# common bash history across multiple terminals
# note: if the prompt is slow to redisplay, you may be useful to disable this
export PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"
export HISTCONTROL=erasedups
shopt -u histappend

# git
# source ~/.git-prompt-export
# alias
alias sync-doc='~/mysrc/sync-script/sync-script.sh'


# ROS
if [ -d "/opt/ros" ]; then
    test "$ROS_DISTRO" = "" && export ROS_DISTRO=foxy
    if [ "$ROS_DISTRO" = "rolling" ]; then
        source /opt/ros/rolling/setup.bash
    elif [ "$ROS_DISTRO" = "foxy" ]; then
        source /opt/ros/foxy/setup.bash
    elif [ "$ROS_DISTRO" = "noetic" ]; then
        source /opt/ros/noetic/setup.bash
    else
        echo "Invalid ROS_DISTRO `$ROS_DISTRO` was given."
    fi

    source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash

    if [ "$ROS_VERSION" = "1" ]; then
        export ROSCONSOLE_FORMAT='[${severity}] [${time}] [${node}]: ${message}'
    elif [ "$ROS_VERSION" = "2" ]; then
        export RCUTILS_CONSOLE_OUTPUT_FORMAT="[{severity} {time}] [{name}]: {message}"
        export RCUTILS_COLORIZED_OUTPUT=1
    fi
fi

if [ -d "$HOME/ros2_ws/install" ]; then
  source $HOME/ros2_ws/install/setup.bash
fi

# Linuxbrew
# test -d /home/linuxbrew/.linuxbrew && eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)

# Fish Shell
if [ -z "$FISH_VERSION" ]; then
    command -v fish > /dev/null 2>&1 && exec fish
fi
