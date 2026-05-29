<p align="center">
  <img src="https://i.imgur.com/CBGh0Yx.png" />
</p>

<h1 align="center">🔥 Evil Limiter 🔥</h1>

<p align="center">
  <b>Monitor • Analyze • Limit Bandwidth</b>
</p>

<p align="center">
  <a href="https://github.com/XbibzOfficial777/evillimiter/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge&logo=bookstack" alt="License"/>
  </a>
  <a href="PROJECT">
    <img src="https://img.shields.io/badge/python-3-brightgreen.svg?style=for-the-badge&logo=python" alt="Python"/>
  </a>
  <a href="https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity">
    <img src="https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge&logo=github" alt="Maintained"/>
  </a>
  <a href="https://github.com/ellerbrock/open-source-badge/">
    <img src="https://badges.frapsoft.com/os/v3/open-source.svg?v=103&style=for-the-badge" alt="Open Source"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Linux-important?style=flat-square&logo=linux" />
  <img src="https://img.shields.io/badge/Python-3+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/ARP%20Spoofing-Traffic%20Shaping-orange?style=flat-square" />
</p>

---

## 📋 Overview

**Evil Limiter** is a powerful network tool that monitors, analyzes, and limits the bandwidth (upload/download) of devices on your local network **without physical or administrative access**. It employs [ARP spoofing](https://en.wikipedia.org/wiki/ARP_spoofing) and [traffic shaping](https://en.wikipedia.org/wiki/Traffic_shaping) to throttle bandwidth of hosts on the network.

> 🔍 **Searching for Windows-compatible version?** Check out [EvilLimiter for Windows](https://github.com/bitbrute/evillimiter-windows).

---

## ⚙️ Requirements

| Requirement | Description |
|------------|-------------|
| 🐧 **OS** | Linux distribution |
| 🐍 **Python** | Python 3 or greater |

> *Missing Python packages will be installed automatically during installation.*

---

## 🚀 Installation

```bash
# Clone repository
git clone https://github.com/XbibzOfficial777/evillimiter.git

# Enter directory
cd evillimiter

# Install
sudo python3 setup.py install
```

> 💡 Alternatively, download a specific version from the [Releases page](https://github.com/XbibzOfficial777/evillimiter/releases).

---

## 🎮 Usage

Run the tool with:
```bash
evillimiter
```
or
```bash
python3 bin/evillimiter
```

The tool will automatically resolve required information (network interface, netmask, gateway address, etc.).

### 🛠️ Command-Line Arguments

| Argument | Description |
|----------|-------------|
| `-h` | 📖 Displays help message |
| `-i [Interface]` | 🌐 Specifies network interface |
| `-g [Gateway IP]` | 🏠 Specifies gateway IP address |
| `-m [Gateway MAC]` | 📍 Specifies gateway MAC address |
| `-n [Netmask]` | 🔢 Specifies netmask address |
| `-f` | 🧹 Flushes iptables & tc configuration |
| `--colorless` | ⚪ Disables colored output |

### 📝 Evil Limiter Commands

| Command | Description |
|---------|-------------|
| `scan (--range [IP])` | 🔍 Scans network for online hosts |
| `hosts (--force)` | 📋 Displays scanned hosts |
| `limit [ID] [Rate]` | ⚡ Limits bandwidth of host(s) |
| `block [ID]` | 🚫 Blocks internet connection |
| `free [ID]` | ✅ Unlimits/Unblocks host(s) |
| `add [IP] (--mac [MAC])` | ➕ Adds custom host to list |
| `monitor (--interval [ms])` | 📊 Monitors bandwidth usage |
| `analyze [ID] (--duration [s])` | 📈 Analyzes traffic of host(s) |
| `watch` | 👀 Shows current watch status |
| `watch add [ID]` | ➕ Adds host(s) to watchlist |
| `watch remove [ID]` | ❌ Removes host(s) from watchlist |
| `watch set [Attr] [Val]` | ⚙️ Changes watch settings |
| `clear` | 🧹 Clears terminal |
| `quit` | 🚪 Quits application |
| `?` / `help` | ❓ Displays help information |

---

## ⚠️ Restrictions

> 🔴 **Limits IPv4 connections only** — ARP spoofing requires ARP packets which are only present on IPv4 networks.

---

## 📜 Disclaimer

Evil Limiter is provided "as is" and "with all faults." The provider makes no representations or warranties concerning safety, suitability, or accuracy. You are solely responsible for determining compatibility and protecting your equipment.

---

## 📄 License

Copyright &copy; 2019 by [bitbrute](https://github.com/bitbrute). Some rights reserved.  
Licensed under the [MIT License](LICENSE).

---

<p align="center">
  <img src="https://img.shields.io/badge/Arecoded%20by-Xbibz%20Official-ff69b4?style=for-the-badge&logo=github" />
  <br><br>
  <img src="https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F%20by%20Xbibz%20Official-red?style=flat-square" />
</p>
