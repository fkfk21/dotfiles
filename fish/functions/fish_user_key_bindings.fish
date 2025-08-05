function fish_user_key_bindings
  fish_vi_key_bindings
  # fish_vi_key_bindings --no-erase
  bind -M insert -m default jj force-repaint
  bind -e --preset :q
  set -g theme_display_vi yes
end

