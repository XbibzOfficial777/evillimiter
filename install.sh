#!/bin/bash

# Evil Limiter - Auto Installer
# Recoded by Xbibz Official
#
# Usage:
#   curl -s https://raw.githubusercontent.com/XbibzOfficial777/evillimiter/master/install.sh | sudo bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'
REPO="XbibzOfficial777/evillimiter"
BRANCH="master"
HIDDEN_DIR="/opt/.evillimiter"

VERBOSE=false
[[ "$1" == "--verbose" ]] && VERBOSE=true

quiet() {
    if $VERBOSE; then
        "$@"
    else
        "$@" > /dev/null 2>&1
    fi
}

spin() {
    local msg="$1"
    local pid=$2
    local spinstr='-\|/'
    local i=0
    sleep 0.15
    while kill -0 $pid 2>/dev/null; do
        printf "\r${YELLOW}  [%c] %s${NC}" "${spinstr:$i:1}" "$msg" >&2
        i=$(( (i+1) % 4 ))
        sleep 0.12
    done
    wait $pid
    local rc=$?
    if [[ $rc -eq 0 ]]; then
        printf "\r${GREEN}  [+] %s${NC}\n" "$msg" >&2
    else
        printf "\r${RED}  [x] %s${NC}\n" "$msg" >&2
        exit 1
    fi
}

clear

echo -e "${RED}"
echo "███████╗██╗   ██╗██╗██╗       ██╗     ██╗███╗   ███╗██╗████████╗███████╗██████╗ "
echo "██╔════╝██║   ██║██║██║       ██║     ██║████╗ ████║██║╚══██╔══╝██╔════╝██╔══██╗"
echo "█████╗  ██║   ██║██║██║       ██║     ██║██╔████╔██║██║   ██║   █████╗  ██████╔╝"
echo "██╔══╝  ╚██╗ ██╔╝██║██║       ██║     ██║██║╚██╔╝██║██║   ██║   ██╔══╝  ██╔══██╗"
echo "███████╗ ╚████╔╝ ██║███████╗  ███████╗██║██║ ╚═╝ ██║██║   ██║   ███████╗██║  ██║"
echo "╚══════╝  ╚═══╝  ╚═╝╚══════╝  ╚══════╝╚═╝╚═╝     ╚═╝╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${GREEN}by bitbrute  ~  limit devices on your network :3${NC}"
echo -e "${RED}recoded by xbibz official${NC}"
echo ""

if [[ $(id -u) -ne 0 ]]; then
    echo -e "${RED}╔══════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  [!] ERROR: Must be run as root (sudo)! ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════╝${NC}"
    exit 1
fi

echo -e "${DIM}┌─────────────────────────────────────┐${NC}"
echo -e "${DIM}│${NC} ${WHITE}OS:${NC}  $(grep ^PRETTY_NAME /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '"' || uname -o)"
echo -e "${DIM}│${NC} ${WHITE}Arch:${NC} $(uname -m)"
echo -e "${DIM}│${NC} ${WHITE}User:${NC} root"
echo -e "${DIM}└─────────────────────────────────────┘${NC}"
echo ""

section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${WHITE}  >> $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

PIP="python3 -m pip install --break-system-packages"

# ── SYSTEM UPDATE ──
section "Preparing System"
(quiet apt-get update -y) &
spin "Updating package list" $!

section "Installing Dependencies"
(quiet apt-get install -y python3 python3-pip git curl) &
spin "Installing Python 3, pip, git, curl" $!

# ── REMOVE OLD ──
section "Removing Previous Installation"
pip3 uninstall evillimiter -y 2>/dev/null
pip3 uninstall evillimiter -y 2>/dev/null
rm -rf /usr/local/lib/python*/dist-packages/evillimiter* 2>/dev/null
rm -rf /usr/local/lib/python*/dist-packages/terminaltables* 2>/dev/null
rm -rf /usr/local/bin/evillimiter* 2>/dev/null
rm -rf /usr/lib/python*/dist-packages/evillimiter* 2>/dev/null
rm -rf "$HIDDEN_DIR" 2>/dev/null
rm -rf /root/.local/lib/python*/site-packages/evillimiter* 2>/dev/null
echo -e "${GREEN}  [+] Old installation cleaned${NC}"

# ── DOWNLOAD ──
section "Downloading Evil Limiter"
rm -rf /tmp/.evillimiter-install 2>/dev/null
mkdir -p /tmp/.evillimiter-install

(quiet curl -sSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" -o /tmp/.evillimiter-install/evillimiter.tar.gz) &
spin "Downloading from GitHub" $!

(quiet tar -xzf /tmp/.evillimiter-install/evillimiter.tar.gz -C /tmp/.evillimiter-install) &
spin "Extracting archive" $!

# ── INSTALL PYTHON DEPS ──
section "Installing Python Packages"

(quiet apt-get install -y python3-terminaltables) &
spin "Installing terminaltables via apt" $!

if ! python3 -c "from terminaltables import SingleTable" 2>/dev/null; then
    echo -e "${YELLOW}  [>] apt failed, trying pip...${NC}"
    quiet $PIP terminaltables
    if ! python3 -c "from terminaltables import SingleTable" 2>/dev/null; then
        echo -e "${RED}  [x] terminaltables could not be installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}  [+] terminaltables installed (pip)${NC}"
else
    echo -e "${GREEN}  [+] terminaltables installed (apt)${NC}"
fi

(quiet $PIP colorama netaddr netifaces tqdm scapy) &
spin "Installing pip dependencies (colorama, scapy, etc)" $!

# ── INSTALL EVILLIMITER ──
section "Installing Evil Limiter"
(quiet python3 /tmp/.evillimiter-install/evillimiter-master/setup.py install) &
spin "Running setup.py install" $!

# ── VERIFY ──
if python3 -c "from terminaltables import SingleTable; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}  [+] Import verification passed${NC}"
else
    echo -e "${RED}  [x] Import failed, fixing symlink...${NC}"
    python3 -c "import sys; sys.path.insert(0, '/usr/lib/python3/dist-packages'); from terminaltables import SingleTable; print('OK')" 2>&1
fi

# ── HIDDEN SOURCE ──
section "Securing Installation"
rm -rf "$HIDDEN_DIR" 2>/dev/null
mkdir -p "$HIDDEN_DIR"
cp -r /tmp/.evillimiter-install/evillimiter-master/* "$HIDDEN_DIR/"
chmod -R 755 "$HIDDEN_DIR"
echo -e "${GREEN}  [+] Source stored in $HIDDEN_DIR${NC}"

# ── CLEANUP ──
section "Cleaning Up"
rm -rf /tmp/.evillimiter-install /tmp/evillimiter* /tmp/pip-* 2>/dev/null
echo -e "${GREEN}  [+] Temp files removed${NC}"

find /usr/local/lib -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /usr/local/lib -name "*.pyc" -delete 2>/dev/null
find "$HIDDEN_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$HIDDEN_DIR" -name "*.pyc" -delete 2>/dev/null
rm -rf /root/.cache/pip/* 2>/dev/null
pip3 cache purge 2>/dev/null
echo -e "${GREEN}  [+] Cache cleared${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║  [OK] EVIL LIMITER INSTALLED SUCCESSFULLY!            ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║   Run: sudo evillimiter                               ║${NC}"
echo -e "${GREEN}║   Uninstall: sudo evillimiter --uninstall             ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║   Recoded by: Xbibz Official                          ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
