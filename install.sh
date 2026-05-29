#!/bin/bash

# Evil Limiter - Auto Installer
# Recoded by Xbibz Official
#
# Run:
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

section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${WHITE}  >> $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

run_step() {
    echo -e "${YELLOW}  [>] $1...${NC}"
}

ok_step() {
    echo -e "${GREEN}  [+] $1${NC}"
}

fail_step() {
    echo -e "${RED}  [x] $1${NC}"
    if [[ -n "$2" ]]; then
        echo -e "${RED}      $2${NC}"
    fi
}

# ── Update & Dependencies ──
section "Preparing System"
run_step "Updating package list"
apt-get update -y 2>&1 | tail -1
ok_step "Package list updated"

section "Installing Dependencies"
run_step "Installing Python 3, pip, git, curl"
apt-get install -y python3 python3-pip git curl 2>&1 | tail -3
ok_step "Dependencies installed"

section "Removing Previous Installation"
run_step "Removing old evillimiter"
pip3 uninstall evillimiter -y 2>/dev/null
pip3 uninstall evillimiter -y 2>/dev/null
rm -rf /usr/local/lib/python*/dist-packages/evillimiter* /usr/local/bin/evillimiter* 2>/dev/null
rm -rf /usr/lib/python*/dist-packages/evillimiter* 2>/dev/null
rm -rf "$HIDDEN_DIR" 2>/dev/null
ok_step "Old installation cleaned"

section "Downloading Evil Limiter"
rm -rf /tmp/.evillimiter-install 2>/dev/null
mkdir -p /tmp/.evillimiter-install
cd /tmp/.evillimiter-install

run_step "Downloading from GitHub"
curl -#L "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" -o evillimiter.tar.gz 2>&1
ok_step "Download complete"

run_step "Extracting archive"
tar -xzf evillimiter.tar.gz
cd "evillimiter-master"
ok_step "Extracted successfully"

section "Installing Python Packages"
run_step "Installing dependencies via pip"
pip3 install --break-system-packages -r requirements.txt 2>&1
if [[ $? -ne 0 ]]; then
    pip3 install -r requirements.txt 2>&1
fi
if [[ $? -ne 0 ]]; then
    fail_step "pip install failed, trying individual packages"
    pip3 install --break-system-packages colorama netaddr netifaces tqdm scapy terminaltables 2>&1 || \
    pip3 install colorama netaddr netifaces tqdm scapy terminaltables 2>&1
    if [[ $? -ne 0 ]]; then
        fail_step "Failed to install Python packages"
        exit 1
    fi
fi
ok_step "Python packages installed"

run_step "Verifying terminaltables"
python3 -c "from terminaltables import SingleTable" 2>&1
if [[ $? -ne 0 ]]; then
    fail_step "terminaltables not installed, trying manually"
    pip3 install terminaltables --break-system-packages 2>&1 || pip3 install terminaltables 2>&1
    python3 -c "from terminaltables import SingleTable" 2>&1
    if [[ $? -ne 0 ]]; then
        fail_step "terminaltables still missing, trying apt"
        apt-get install -y python3-terminaltables 2>/dev/null || true
    fi
fi
ok_step "All dependencies verified"

section "Installing Evil Limiter"
run_step "Running setup.py install"
python3 setup.py install 2>&1
if [[ $? -eq 0 ]]; then
    ok_step "Evil Limiter installed successfully"
else
    fail_step "Installation failed"
    exit 1
fi

section "Securing Installation"
run_step "Storing source in hidden directory"
cd /tmp/.evillimiter-install
rm -rf "$HIDDEN_DIR" 2>/dev/null
mkdir -p "$HIDDEN_DIR"
cp -r evillimiter-master/* "$HIDDEN_DIR/"
chmod -R 755 "$HIDDEN_DIR"
ok_step "Source stored in $HIDDEN_DIR"

section "Cleaning Up"
run_step "Removing temporary files"
rm -rf /tmp/.evillimiter-install /tmp/evillimiter* /tmp/pip-* 2>/dev/null
ok_step "Temp files removed"

run_step "Removing build cache"
find /usr/local/lib -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /usr/local/lib -name "*.pyc" -delete 2>/dev/null
find /usr/local/lib -name "*.pyo" -delete 2>/dev/null
find "$HIDDEN_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$HIDDEN_DIR" -name "*.pyc" -delete 2>/dev/null
ok_step "Cache cleared"

run_step "Cleaning pip cache"
rm -rf /root/.cache/pip/* 2>/dev/null
pip3 cache purge 2>/dev/null
ok_step "Pip cache cleaned"

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
