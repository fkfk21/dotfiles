" Macro and key setting
  " jj become esc
  inoremap jj <ESC>
  " esc * 2 delete highlight
  nmap <silent> <ESC><ESC> :nohlsearch<CR>

" move center search word
  nnoremap n nzz
  nnoremap N Nzz
  nnoremap * *zz
  nnoremap # #z
  nnoremap g* g*zz
  nnoremap g#  g#zz

" make delete command not yunk
  nnoremap d "_d
  nnoremap x "_x
  xnoremap d "_d
  xnoremap p "_dP

" indent settings
  nnoremap > >>
  nnoremap < <<

" move from neo-tree back to editor
augroup NeoTreeKeymaps
  autocmd!
  autocmd FileType neo-tree nnoremap <silent><buffer> <C-f> <C-w>p
augroup END
