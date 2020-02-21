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

" move center search word
  nnoremap n nzz
  nnoremap N Nzz
  nnoremap * *zz
  nnoremap # #z
  nnoremap g* g*zz
  nnoremap g#  g#zz

" jump definition
  set tags=./tags;






