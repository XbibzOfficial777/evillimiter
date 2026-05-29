#!/bin/bash

# Evil Limiter - Auto Installer
# Recoded by Xbibz Official
#
# Run:
#   curl -s https://raw.githubusercontent.com/XbibzOfficial777/evillimiter/master/install.sh | sudo bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
REPO="XbibzOfficial777/evillimiter"
BRANCH="master"

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
    echo -e "${RED}[!] This script must be run as root (sudo)!${NC}"
    exit 1
fi

echo -e "${YELLOW}[*] Updating package list...${NC}"
apt-get update -y

echo -e "${YELLOW}[*] Installing dependencies (python3, pip, curl)...${NC}"
apt-get install -y python3 python3-pip curl

echo -e "${YELLOW}[*] Downloading Evil Limiter via curl...${NC}"
cd /tmp
rm -rf evillimiter-master evillimiter 2>/dev/null

# Download tarball from raw GitHub
curl -sL "https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz" -o evillimiter.tar.gz
tar -xzf evillimiter.tar.gz
cd "evillimiter-master"

echo -e "${YELLOW}[*] Installing Python dependencies...${NC}"
pip3 install -r requirements.txt 2>/dev/null

echo -e "${YELLOW}[*] Installing Evil Limiter...${NC}"
python3 setup.py install

cd /tmp
rm -rf evillimiter-master evillimiter.tar.gz 2>/dev/null

echo ""
echo -e "${GREEN}[✓] Installation complete!${NC}"
echo -e "${CYAN}Run: sudo evillimiter${NC}"
echo ""
