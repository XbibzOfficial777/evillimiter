#!/bin/bash

# Evil Limiter - Auto Installer
# Recoded by Xbibz Official
#
# Run:
#   curl -s https://raw.githubusercontent.com/XbibzOfficial777/evillimiter/master/install.sh | sudo bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'
REPO="XbibzOfficial777/evillimiter"
BRANCH="master"
HIDDEN_DIR="/opt/.evillimiter"

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

spinner() {
    local pid=$1
    local msg="$2"
    local spin='-\|/'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i+1) % 4 ))
        printf "\r${CYAN}[${spin:$i:1}]${NC} ${msg}..."
        sleep 0.1
    done
    printf "\r${GREEN}[+]${NC} ${msg}... ${GREEN}Done${NC}\n"
}

section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${WHITE}  >> $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

step() {
    local msg="$1"
    shift
    ("$@") &>/dev/null &
    local pid=$!
    spinner "$pid" "$msg"
    wait "$pid"
    return $?
}

if [[ $EUID -ne 0 ]]; then
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

section "Preparing System"
step "Updating package list" apt-get update -y

section "Installing Dependencies"
step "Installing Python 3 & tools" apt-get install -y python3 python3-pip curl

section "Removing Previous Installation"
echo -e "${YELLOW}  [>] Removing old evillimiter (if any)...${NC}"
pip3 uninstall evillimiter -y 2>/dev/null
rm -rf /usr/local/lib/python*/dist-packages/evillimiter* /usr/local/bin/evillimiter* 2>/dev/null
rm -rf /usr/lib/python*/dist-packages/evillimiter* 2>/dev/null
rm -rf "$HIDDEN_DIR" 2>/dev/null
echo -e "${GREEN}  [+] Clean${NC}"

section "Downloading Evil Limiter"
rm -rf /tmp/.evillimiter-install 2>/dev/null
mkdir -p /tmp/.evillimiter-install
cd /tmp/.evillimiter-install

echo -e "${YELLOW}  [>] Downloading from GitHub...${NC}"
curl -#L "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" -o evillimiter.tar.gz 2>&1 | while IFS= read -r line; do
    if [[ "$line" =~ [0-9]+% ]]; then
        echo -ne "\r${CYAN}  [~] Progress: ${line}${NC}   "
    fi
done
echo -e "\r${GREEN}  [+] Download complete!${NC}   "

echo -e "${YELLOW}  [>] Extracting archive...${NC}"
tar -xzf evillimiter.tar.gz
cd "evillimiter-master"
echo -e "${GREEN}  [+] Extracted successfully${NC}"

section "Installing Python Packages"
step "Installing dependencies (colorama, scapy, etc)" pip3 install -r requirements.txt

section "Installing Evil Limiter"
echo -e "${YELLOW}  [*] Running setup.py install...${NC}"
python3 setup.py install 2>&1 | while IFS= read -r line; do
    if [[ "$line" == *"Finished"* ]]; then
        echo -e "${GREEN}  [+] $line${NC}"
    elif [[ -n "$line" ]]; then
        echo -e "     ${DIM}$line${NC}"
    fi
done

section "Securing Installation"
echo -e "${YELLOW}  [>] Moving source to hidden directory...${NC}"
cd /tmp/.evillimiter-install
rm -rf "$HIDDEN_DIR" 2>/dev/null
mkdir -p "$HIDDEN_DIR"
cp -r evillimiter-master/* "$HIDDEN_DIR/"
chmod -R 755 "$HIDDEN_DIR"
echo -e "${GREEN}  [+] Source stored in $HIDDEN_DIR${NC}"

section "Cleaning Up"
echo -e "${YELLOW}  [>] Removing temporary files...${NC}"
rm -rf /tmp/.evillimiter-install 2>/dev/null
echo -e "${GREEN}  [+] Temp files removed${NC}"

echo -e "${YELLOW}  [>] Removing build cache...${NC}"
find /usr/local/lib/python*/dist-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /usr/local/lib/python*/dist-packages -name "*.pyc" -delete 2>/dev/null
find /usr/local/lib/python*/dist-packages -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null
echo -e "${GREEN}  [+] Cache cleared${NC}"

echo -e "${YELLOW}  [>] Cleaning pip cache...${NC}"
pip3 cache purge 2>/dev/null
echo -e "${GREEN}  [+] Pip cache cleaned${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║  [OK] EVIL LIMITER INSTALLED SUCCESSFULLY!            ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║   Run:                                                ${GREEN}║${NC}"
echo -e "${GREEN}║   sudo evillimiter                                    ${GREEN}║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║   Uninstall:                                          ${GREEN}║${NC}"
echo -e "${GREEN}║   sudo evillimiter --uninstall                        ${GREEN}║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║   Recoded by: Xbibz Official                          ${GREEN}║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
