<div align="center">
  <img src="https://i.vgy.me/tfrvUe.jpg" width="200"/>
  <h1>Evil Limiter</h1>
  <p><b>Monitor / Analyze / Limit Bandwidth</b></p>
  <p>
    <a href="https://github.com/XbibzOfficial777/evillimiter/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge&logo=bookstack" alt="License"/>
    </a>
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/python-3-brightgreen.svg?style=for-the-badge&logo=python" alt="Python 3"/>
    </a>
    <img src="https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge&logo=github" alt="Maintained"/>
    <img src="https://badges.frapsoft.com/os/v3/open-source.svg?v=103&style=for-the-badge" alt="Open Source"/>
    <img src="https://img.shields.io/badge/version-2.0.2-blue?style=for-the-badge"/>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Platform-Linux-important?style=flat-square&logo=linux"/>
    <img src="https://img.shields.io/badge/Python-3+-blue?style=flat-square&logo=python"/>
    <img src="https://img.shields.io/badge/ARP_Spoofing-Traffic_Shaping-orange?style=flat-square"/>
    <img src="https://img.shields.io/badge/IPv4+IPv6-Dual_Stack-ff69b4?style=flat-square"/>
  </p>
  <br>
  <img src="https://img.shields.io/badge/Recoded_by-Xbibz_Official-ff69b4?style=for-the-badge&logo=github"/>
</div>

---

## Overview

A tool to monitor, analyze and limit the bandwidth (upload/download) of devices on your local network **without physical or administrative access**.  
Evil Limiter employs [ARP spoofing](https://en.wikipedia.org/wiki/ARP_spoofing) / [NDP spoofing](https://en.wikipedia.org/wiki/Neighbor_Discovery_Protocol) and [traffic shaping](https://en.wikipedia.org/wiki/Traffic_shaping) to throttle the bandwidth of hosts on the network.

> **v2.0+** — Now with **dual-stack IPv4 + IPv6** support!

---

## Features

| Feature | Description |
|---------|-------------|
| **Dual-Stack** | IPv4 + IPv6 auto-detection and simultaneous spoofing |
| **Persistent Limits** | Per-MAC limits saved to file, auto-reapply on restart |
| **Non-Interactive Mode** | Scriptable CLI for automation |
| **Block All / Unblock All** | One command to block or free every host |
| **Live Graph** | Real-time ASCII bandwidth chart per host |
| **Sniffer Mode** | Promiscuous monitoring without spoofing |
| **Bypass Detection** | Detects static ARP / anti-ARP-spoof countermeasures |
| **Bandwidth Monitor** | Real-time bandwidth usage display |
| **Traffic Analysis** | Per-host upload/download analysis with bar charts |
| **Flapping** | Alternating block/free intervals |
| **Reconnection Watch** | Auto-detect IP changes and re-apply limits |
| **Config File** | `/opt/.evillimiter/config.json` for defaults |

---

## Requirements

| Requirement | Description |
|-------------|-------------|
| **OS** | Linux distribution |
| **Python** | Python 3 or greater |

---

## Installation

### Option 1 — Auto Install (recommended)

```bash
curl -s https://raw.githubusercontent.com/XbibzOfficial777/evillimiter/master/install.sh | sudo bash
```

### Option 2 — Manual

```bash
git clone https://github.com/XbibzOfficial777/evillimiter.git
cd evillimiter
sudo python3 setup.py install
```

### Option 3 — Download Release

Download from [Releases page](https://github.com/XbibzOfficial777/evillimiter/releases).

## Uninstall

```bash
sudo evillimiter --uninstall
```

Or if the Python module is broken:

```bash
curl -s https://raw.githubusercontent.com/XbibzOfficial777/evillimiter/master/uninstall.sh | sudo bash
```

---

## Usage

```bash
sudo evillimiter
```

The tool will automatically resolve required information (network interface, netmask, gateway address, etc.).

### Arguments

| Argument | Description |
|----------|-------------|
| `-h` | Help message |
| `-i [Interface]` | Network interface |
| `-g [Gateway IP]` | Gateway IP address |
| `-m [Gateway MAC]` | Gateway MAC address |
| `-n [Netmask]` | Netmask address |
| `-f` | Flush iptables & tc config |
| `-c` | Cleanup all rules and disable forwarding |
| `--colorless` | Disable colored output |
| `-v` | Show version |
| `--uninstall` | Completely remove evillimiter |
| `--sniffer` | Monitor without spoofing (promiscuous) |

### Non-Interactive Mode (Scripting)

| Argument | Description |
|----------|-------------|
| `--limit-ip [IP]` | Limit bandwidth for host (requires `--rate`) |
| `--block-ip [IP]` | Block internet for host |
| `--unblock-ip [IP]` | Free host |
| `--rate [RATE]` | Rate for `--limit-ip` (e.g. `500kbit`, `1mbit`) |
| `--direction [dir]` | `upload`, `download`, or `both` (default: both) |

Examples:
```bash
# Limit a device to 500kbit
sudo evillimiter --limit-ip 192.168.1.100 --rate 500kbit

# Block a device
sudo evillimiter --block-ip 192.168.1.100

# Unblock a device
sudo evillimiter --unblock-ip 192.168.1.100
```

### Commands

| Command | Description |
|---------|-------------|
| `scan (--range [IP])` | Scan network for hosts |
| `hosts (--force)` | Show scanned hosts with bypass status |
| `limit [ID] [Rate]` | Limit bandwidth |
| `block [ID]` | Block internet |
| `free [ID]` | Unlimit/Unblock host |
| `blockall` | Block ALL hosts at once |
| `unblockall` | Free ALL hosts at once |
| `graph (--interval [ms]) (--duration [s])` | Live bandwidth graph |
| `add [IP] (--mac [MAC])` | Add custom host |
| `monitor (--interval [ms])` | Monitor bandwidth |
| `analyze [ID] (--duration [s])` | Analyze traffic with bar charts |
| `flap [ID] (--block [s]) (--free [s])` | Alternating block/free |
| `watch` | Watch status |
| `watch add [ID]` | Add to watchlist |
| `watch remove [ID]` | Remove from watchlist |
| `watch set [Attr] [Val]` | Change watch settings |
| `sort [field]` | Sort by ip/name/mac/id/status |
| `select [ID]` | Select host |
| `clear` | Clear terminal |
| `quit` / `exit` | Quit |
| `?` / `help` | Help |

---

## Default Rate

Edit `/opt/.evillimiter/config.json` to set default rate:

```json
{
  "default_rate": "500kbit",
  "default_direction": "both",
  "sniffer_mode": false,
  "autosave_limits": true
}
```

---

## Disclaimer

Provided "as is" without warranty. You are solely responsible for use of this software.

---

## License

Copyright &copy; 2019 by [bitbrute](https://github.com/bitbrute). Some rights reserved.  
Licensed under the [MIT License](LICENSE).

---

<div align="center">
  <br>
  <img src="https://img.shields.io/badge/Recoded_by-Xbibz_Official-red?style=for-the-badge"/>
  <br><br>
  <sub>Evil Limiter v2.0.2 — Network Bandwidth Limiter Tool</sub>
</div>
