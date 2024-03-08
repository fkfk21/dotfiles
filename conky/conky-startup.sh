#!/bin/sh

if [ "$DESKTOP_SESSION" = "ubuntu" ]; then 
   # No widgets enabled!
   env LC_ALL=en_US.utf8 conky -c $HOME/dotfiles/conky/_conkyrc
   exit 0
fi
