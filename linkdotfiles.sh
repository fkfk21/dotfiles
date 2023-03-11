#!/bin/sh

ln -sf ~/dotfiles/.bashrc ~/.bashrc
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
mkdir -p ~/.config/Code/User
ln -sf ~/dotfiles/settings.json ~/.config/Code/User/settings.json
ln -sf ~/dotfiles/keybindings.json ~/.config/Code/User/keybindings.json

# fish
mkdir -p ~/.config/fish/conf.d
ln -sf ~/dotfiles/fish/config.fish ~/.config/fish/config.fish
ln -sf ~/dotfiles/fish/bobthefish_config.fish ~/.config/fish/conf.d/bobthefish_config.fish
ln -sf ~/dotfiles/fish/fish_plugins ~/.config/fish/fish_plugins
ln -sf ~/dotfiles/fish/completions/poetry.fish ~/.config/fish/completions/poetry.fish

# terminator
mkdir -p ~/.config/terminator
ln -sf ~/dotfiles/terminator/config ~/.config/terminator/config
