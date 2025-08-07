set nocompatible

" gyousuuhyouji
  set tabstop=2
  set shiftwidth=2
  set expandtab
  set smartindent

" Search setting
  set ignorecase        " distinguish uppercase letter and lowercase letter
  set smartcase         " if there is uppercase in serch letter, distinguish
  set incsearch         " incremental serach
  set hlsearch          " hilight


" Edit Settings
  set shiftround        " '>'or'<' indent become 'shiftwidth' multiple
  set infercase         " do not distinguish upper or not when complement
  set hidden            " hide buffer instead of close to leave undo history
  set switchbuf=useopen " open buffer which is opend already instead of new
  set showmatch         " display highlight corresponding backets
  set matchtime=3       " display corresponding backets highlight time = 3

  set matchpairs& matchpairs+=<:>   " add backets match pair < >

  set backspace=indent,eol,start    " backspace can delete all type

  " unuse swap file & backup file
  set nowritebackup
  set nobackup
  set noswapfile

" Display settings
  set number            " display row number
 
" Macro and key setting
  " jj become esc
  inoremap jj <ESC>
  " esc * 2 delete highlight
  nmap <silent> <ESC><ESC> :nohlsearch<CR>
  " change paste command
  " nnoremap p P

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


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"                          dein 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""" dein installation
let s:DEIN_VERSION = '3.1'
let $CACHE = expand('~/.cache')
if !($CACHE->isdirectory())
  call mkdir($CACHE, 'p')
endif
if &runtimepath !~# '/dein.vim'
  let s:dir = 'dein.vim'->fnamemodify(':p')
  if !(s:dir->isdirectory())
    let s:dir = $CACHE .. '/dein/repos/github.com/Shougo/dein.vim'
    if !(s:dir->isdirectory())
      execute '!git clone -b' s:DEIN_VERSION 'https://github.com/Shougo/dein.vim' s:dir
    endif
  endif
  execute 'set runtimepath^='
        \ .. s:dir->fnamemodify(':p')->substitute('[/\\]$', '', '')
endif

""""" dein configuration
let s:dein_base = '~/.cache/dein'
let s:dein_src = '~/.cache/dein/repos/github.com/Shougo/dein.vim'

" Set dein runtime path
execute 'set runtimepath+=' . s:dein_src

" dein initialization
call dein#begin(s:dein_base)

call dein#add(s:dein_src)

"" Add plugins


call dein#end()

" Attempt to determine the type of a file based on its name and possibly its
" contents. Use this to allow intelligent auto-indenting for each filetype,
" and for plugins that are filetype specific.
if has('filetype')
  filetype indent plugin on
endif


" Enable syntax highlighting
if has('syntax')
  syntax on
endif

" Uncomment if you want to install not-installed plugins on startup.
"if dein#check_install()
"  call dein#install()
"endif






