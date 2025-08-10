"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"                          dein 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"" settings for nvim version 0.7.2
lua vim.loader.enable()

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

""" dein initialization
call dein#begin(s:dein_base)
call dein#add(s:dein_src)

"" Add plugins
" call dein#add('Shougo/neosnippet.vim')

" 補完用
call dein#add('neoclide/coc.nvim', {'rev': 'v0.0.82'})

" 複数行編集用プラグイン
call dein#add('mg979/vim-visual-multi')

" Plugins for neo-tree
call dein#add('nvim-lua/plenary.nvim')
call dein#add('MunifTanjim/nui.nvim')
call dein#add('nvim-neo-tree/neo-tree.nvim', {
      \ 'depends': ['nvim-lua/plenary.nvim', 'MunifTanjim/nui.nvim'],
      \ })
call dein#add('nvim-tree/nvim-web-devicons')
call dein#add('antosha417/nvim-lsp-file-operations')
call dein#add('folke/snacks.nvim')
call dein#add('s1n7ax/nvim-window-picker')

" インデント
call dein#add('lukas-reineke/indent-blankline.nvim' , {'rev': 'v3.6.2'})

" Color Schemes (syntax highlighting)
call dein#add('nvim-treesitter/nvim-treesitter')
call dein#add('vim-scripts/scrollcolors')
call dein#add('sainnhe/gruvbox-material')
call dein#add('morhetz/gruvbox')
call dein#add('rafi/awesome-vim-colorschemes')
call dein#add('tomasiser/vim-code-dark')
call dein#add('folke/tokyonight.nvim')
call dein#add('EdenEast/nightfox.nvim')
call dein#add('nyoom-engineering/oxocarbon.nvim')
call dein#add('rebelot/kanagawa.nvim')
call dein#add('catppuccin/nvim')

" Airline
call dein#add('vim-airline/vim-airline')
call dein#add('vim-airline/vim-airline-themes')


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
if dein#check_install()
  call dein#install()
endif


