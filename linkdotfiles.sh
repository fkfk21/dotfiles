#!/bin/sh

ln -sf ~/dotfiles/.vimrc ~/.vimrc
ln -sf ~/dotfiles/.gitconfig ~/.gitconfig

ln -sf ~/dotfiles/.git-prompt.sh ~/.git-prompt.sh
ln -sf ~/dotfiles/.git-prompt-export ~/.git-prompt-export

prom="source ~/.git-prompt-export"
grep "$prom" ~/.bashrc
if [ $? = 0 ]; then
  echo "$prom :: exist in .bashrc"
else
  echo "$prom :: not exist in .bashrc"
  echo $prom >> ~/.bashrc
fi

# vscode
ln -sf ~/dotfiles/settings.json ~/.config/Code/User/settings.json
ln -sf ~/dotfiles/keybindings.json ~/.config/Code/User/keybindings.json
