#!/bin/bash

# Evil Limiter - Uninstaller
# Recoded by Xbibz Official
#
# Usage:
#   curl -s https://raw.githubusercontent.com/XbibzOfficial777/evillimiter/master/uninstall.sh | sudo bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${RED}"
echo "  ██╗   ██╗███╗   ██╗██╗███╗   ██╗███████╗████████╗ █████╗ ██╗     ██╗"
echo "  ██║   ██║████╗  ██║██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║     ██║"
echo "  ██║   ██║██╔██╗ ██║██║██╔██╗ ██║███████╗   ██║   ███████║██║     ██║"
echo "  ██║   ██║██║╚██╗██║██║██║╚██╗██║╚════██║   ██║   ██╔══██║██║     ██║"
echo "  ╚██████╔╝██║ ╚████║██║██║ ╚████║███████║   ██║   ██║  ██║███████╗██║"
echo "   ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝"
echo -e "${NC}"
echo -e "${GREEN}Uninstaller - Recoded by Xbibz Official${NC}"
echo ""

if [[ $(id -u) -ne 0 ]]; then
    echo -e "${RED}[!] Must be run as root (sudo)!${NC}"
    exit 1
fi

echo -e "${YELLOW}[>] Cleaning network settings...${NC}"
iptables -F 2>/dev/null
iptables -t nat -F 2>/dev/null
iptables -t mangle -F 2>/dev/null
tc qdisc del dev $(ip route | grep default | awk '{print $5}') root 2>/dev/null
echo 0 > /proc/sys/net/ipv4/ip_forward 2>/dev/null
echo -e "${GREEN}[+] Network settings cleaned${NC}"

echo -e "${YELLOW}[>] Uninstalling pip packages...${NC}"
pip3 uninstall evillimiter -y 2>/dev/null
pip3 uninstall evillimiter -y 2>/dev/null
echo -e "${GREEN}[+] Pip packages removed${NC}"

echo -e "${YELLOW}[>] Removing files...${NC}"
rm -rf /usr/local/lib/python*/dist-packages/evillimiter* 2>/dev/null
rm -rf /usr/local/bin/evillimiter* 2>/dev/null
rm -rf /usr/bin/evillimiter* 2>/dev/null
rm -rf /usr/lib/python*/dist-packages/evillimiter* 2>/dev/null
rm -rf /opt/.evillimiter 2>/dev/null
rm -rf /root/.local/lib/python*/site-packages/evillimiter* 2>/dev/null
rm -rf /home/*/.local/lib/python*/site-packages/evillimiter* 2>/dev/null
rm -rf /tmp/.evillimiter-install /tmp/evillimiter* 2>/dev/null
echo -e "${GREEN}[+] Files removed${NC}"

echo -e "${YELLOW}[>] Cleaning cache...${NC}"
find /usr/local/lib -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /usr/local/lib -name "*.pyc" -delete 2>/dev/null
rm -rf /root/.cache/pip/* 2>/dev/null
pip3 cache purge 2>/dev/null
echo -e "${GREEN}[+] Cache cleaned${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  [OK] EVIL LIMITER UNINSTALLED!          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
