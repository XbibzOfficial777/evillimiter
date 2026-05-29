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

run() {
    echo -e "${YELLOW}  [>] $1${NC}"
}

ok() {
    echo -e "${GREEN}  [+] $1${NC}"
}

fail() {
    echo -e "${RED}  [x] $1${NC}"
    if [[ -n "$2" ]]; then
        echo -e "${RED}      $2${NC}"
    fi
}

PIP="python3 -m pip install --break-system-packages"

# ── SYSTEM UPDATE ──
section "Preparing System"
run "Updating package list"
apt-get update -y 2>&1 | tail -1
ok "Package list updated"

section "Installing Dependencies"
run "Installing Python 3, pip, git, curl"
apt-get install -y python3 python3-pip git curl 2>&1 | tail -3
ok "Base dependencies installed"

# ── REMOVE OLD ──
section "Removing Previous Installation"
run "Cleaning old evillimiter completely"
pip3 uninstall evillimiter -y 2>/dev/null
pip3 uninstall evillimiter -y 2>/dev/null
rm -rf /usr/local/lib/python*/dist-packages/evillimiter* 2>/dev/null
rm -rf /usr/local/lib/python*/dist-packages/terminaltables* 2>/dev/null
rm -rf /usr/local/bin/evillimiter* 2>/dev/null
rm -rf /usr/lib/python*/dist-packages/evillimiter* 2>/dev/null
rm -rf "$HIDDEN_DIR" 2>/dev/null
rm -rf /root/.local/lib/python*/site-packages/evillimiter* 2>/dev/null
ok "Old installation cleaned"

# ── DOWNLOAD ──
section "Downloading Evil Limiter"
rm -rf /tmp/.evillimiter-install 2>/dev/null
mkdir -p /tmp/.evillimiter-install
cd /tmp/.evillimiter-install

run "Downloading from GitHub"
curl -#L "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" -o evillimiter.tar.gz 2>&1
ok "Download complete"

run "Extracting archive"
tar -xzf evillimiter.tar.gz
cd "evillimiter-master"
ok "Extracted successfully"

# ── INSTALL PYTHON DEPS ──
section "Installing Python Packages"

# terminaltables pakai apt saja (biar system-wide, no PEP 668 issue)
run "Installing terminaltables via apt"
apt-get install -y python3-terminaltables 2>&1 | tail -2
if python3 -c "from terminaltables import SingleTable" 2>/dev/null; then
    ok "terminaltables installed (apt)"
else
    fail "apt install failed, trying pip"
    $PIP terminaltables 2>&1
    if python3 -c "from terminaltables import SingleTable" 2>/dev/null; then
        ok "terminaltables installed (pip)"
    else
        fail "terminaltables could not be installed"
        exit 1
    fi
fi

# Sisanya via pip with --break-system-packages
run "Installing pip dependencies (colorama, scapy, etc)"
$PIP colorama netaddr netifaces tqdm scapy 2>&1
if [[ $? -eq 0 ]]; then
    ok "Python packages installed"
else
    fail "pip install failed"
    exit 1
fi

# ── INSTALL EVILLIMITER ──
section "Installing Evil Limiter"
run "Running setup.py install"
python3 setup.py install 2>&1
if [[ $? -eq 0 ]]; then
    ok "Evil Limiter installed"
else
    fail "Installation failed"
    exit 1
fi

# ── VERIFY ──
run "Verifying installation"
python3 -c "from terminaltables import SingleTable; print('OK')" 2>&1
if [[ $? -eq 0 ]]; then
    ok "Import verification passed"
else
    fail "Import failed, fixing symlink..."
    python3 -c "import sys; sys.path.insert(0, '/usr/lib/python3/dist-packages'); from terminaltables import SingleTable; print('OK')" 2>&1
fi

# ── HIDDEN SOURCE ──
section "Securing Installation"
run "Storing source in hidden directory"
cd /tmp/.evillimiter-install
rm -rf "$HIDDEN_DIR" 2>/dev/null
mkdir -p "$HIDDEN_DIR"
cp -r evillimiter-master/* "$HIDDEN_DIR/"
chmod -R 755 "$HIDDEN_DIR"
ok "Source stored in $HIDDEN_DIR"

# ── CLEANUP ──
section "Cleaning Up"
run "Removing temporary files"
rm -rf /tmp/.evillimiter-install /tmp/evillimiter* /tmp/pip-* 2>/dev/null
ok "Temp files removed"

run "Removing cache"
find /usr/local/lib -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /usr/local/lib -name "*.pyc" -delete 2>/dev/null
find "$HIDDEN_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$HIDDEN_DIR" -name "*.pyc" -delete 2>/dev/null
rm -rf /root/.cache/pip/* 2>/dev/null
pip3 cache purge 2>/dev/null
ok "Cache cleared"

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
