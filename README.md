<div align="center">
  <img src="https://i.imgur.com/CBGh0Yx.png" width="200"/>
  <h1>🔥 Evil Limiter 🔥</h1>
  <p><b>Monitor • Analyze • Limit Bandwidth</b></p>
  <p>
    <a href="https://github.com/XbibzOfficial777/evillimiter/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge&logo=bookstack" alt="License"/>
    </a>
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/python-3-brightgreen.svg?style=for-the-badge&logo=python" alt="Python 3"/>
    </a>
    <img src="https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge&logo=github" alt="Maintained"/>
    <img src="https://badges.frapsoft.com/os/v3/open-source.svg?v=103&style=for-the-badge" alt="Open Source"/>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Platform-Linux-important?style=flat-square&logo=linux"/>
    <img src="https://img.shields.io/badge/Python-3+-blue?style=flat-square&logo=python"/>
    <img src="https://img.shields.io/badge/ARP%20Spoofing-Traffic%20Shaping-orange?style=flat-square"/>
  </p>
  <br>
  <img src="https://img.shields.io/badge/Arecoded%20by-Xbibz%20Official-ff69b4?style=for-the-badge&logo=github"/>
</div>

---

## 📋 Overview

A tool to monitor, analyze and limit the bandwidth (upload/download) of devices on your local network **without physical or administrative access**.  
Evil Limiter employs [ARP spoofing](https://en.wikipedia.org/wiki/ARP_spoofing) and [traffic shaping](https://en.wikipedia.org/wiki/Traffic_shaping) to throttle the bandwidth of hosts on the network.

> 🔍 **Windows version?** Check out [EvilLimiter for Windows](https://github.com/bitbrute/evillimiter-windows).

---

## ⚙️ Requirements

| Requirement | Description |
|-------------|-------------|
| 🐧 **OS** | Linux distribution |
| 🐍 **Python** | Python 3 or greater |

---

## 🚀 Installation

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

---

## 🎮 Usage

```bash
sudo evillimiter
```

The tool will automatically resolve required information (network interface, netmask, gateway address, etc.).

### 🛠️ Arguments

| Argument | Description |
|----------|-------------|
| `-h` | 📖 Help message |
| `-i [Interface]` | 🌐 Network interface |
| `-g [Gateway IP]` | 🏠 Gateway IP address |
| `-m [Gateway MAC]` | 📍 Gateway MAC address |
| `-n [Netmask]` | 🔢 Netmask address |
| `-f` | 🧹 Flush iptables & tc config |
| `--colorless` | ⚪ Disable colored output |

### 📝 Commands

| Command | Description |
|---------|-------------|
| `scan (--range [IP])` | 🔍 Scan network for hosts |
| `hosts (--force)` | 📋 Show scanned hosts |
| `limit [ID] [Rate]` | ⚡ Limit bandwidth |
| `block [ID]` | 🚫 Block internet |
| `free [ID]` | ✅ Unlimit/Unblock host |
| `add [IP] (--mac [MAC])` | ➕ Add custom host |
| `monitor (--interval [ms])` | 📊 Monitor bandwidth |
| `analyze [ID] (--duration [s])` | 📈 Analyze traffic |
| `watch` | 👀 Watch status |
| `watch add [ID]` | ➕ Add to watchlist |
| `watch remove [ID]` | ❌ Remove from watchlist |
| `watch set [Attr] [Val]` | ⚙️ Change watch settings |
| `clear` | 🧹 Clear terminal |
| `quit` | 🚪 Quit |
| `?` / `help` | ❓ Help |

---

## ⚠️ Restrictions

> 🔴 **IPv4 only** — ARP spoofing requires ARP packets only present on IPv4 networks.

---

## 📜 Disclaimer

Provided "as is" without warranty. You are solely responsible for use of this software.

---

## 📄 License

Copyright &copy; 2019 by [bitbrute](https://github.com/bitbrute). Some rights reserved.  
Licensed under the [MIT License](LICENSE).

---

<div align="center">
  <br>
  <img src="https://img.shields.io/badge/Recoded%20with%20%E2%9D%A4%EF%B8%8F%20by-Xbibz%20Official-red?style=for-the-badge"/>
  <br><br>
  <sub>Evil Limiter — Network Bandwidth Limiter Tool</sub>
</div>
