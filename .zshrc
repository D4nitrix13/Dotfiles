#
# ~/.zshrc
#
# Configuracion de zsh. Sustituye a la de cachyos-zsh-config, que solo
# aportaba un preset de fabrica: esta hace lo mismo y es tuya.
#
# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# GitLab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me
#

# Powerlevel10k: el prompt instantáneo debe quedarse al principio, antes de
# nada que pida una entrada por consola.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Oh My Zsh
export ZSH="/usr/share/oh-my-zsh"
DISABLE_MAGIC_FUNCTIONS="true"
ENABLE_CORRECTION="true"
COMPLETION_WAITING_DOTS="true"
plugins=(git fzf extract)
source $ZSH/oh-my-zsh.sh

# Historial
export HISTCONTROL=ignoreboth
export HISTORY_IGNORE="(\&|[bf]g|c|clear|history|exit|q|pwd|* --help)"
export PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

# Colores en las paginas de man
export LESS_TERMCAP_md="$(tput bold 2> /dev/null; tput setaf 2 2> /dev/null)"
export LESS_TERMCAP_me="$(tput sgr0 2> /dev/null)"

# Alias
alias make="make -j`nproc`"
alias ninja="ninja -j`nproc`"
alias n="ninja"
alias c="clear"
alias rmpkg="sudo pacman -Rsn"
alias cleanch="sudo pacman -Scc"
alias fixpacman="sudo rm /var/lib/pacman/db.lck"
alias update="sudo pacman -Syu"
alias apt="man pacman"
alias apt-get="man pacman"
alias please="sudo"
alias tb="nc termbin.com 9999"
alias cleanup="sudo pacman -Rsn $(pacman -Qtdq)"
alias jctl="journalctl -p 3 -xb"
alias rip="expac --timefmt='%Y-%m-%d %T' '%l\t%n %v' | sort | tail -200 | nl"

# Complementos. El orden importa: el resaltado de sintaxis tiene que cargarse
# el ultimo, porque modifica las reglas de los demas.
source /usr/share/zsh-theme-powerlevel10k/powerlevel10k.zsh-theme
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh

# Sugerencia de comandos de los paquetes instalados
source /usr/share/doc/pkgfile/command-not-found.zsh

# Tu configuracion propia de Powerlevel10k
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

export FZF_BASE=/usr/share/fzf
