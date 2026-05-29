# AGENTS.md — Evil Limiter

## Entrypoint

- App entry: `evillimiter/evillimiter.py:run()` — registered as console_script `evillimiter` in `setup.py:45`
- Version defined in `evillimiter/__init__.py` (`__version__ = '2.0.0'`)
- No tests, no CI, no lint/typecheck config in repo

## Must run as root

- Tool requires `sudo` for ARP spoofing, iptables, tc. Hard check at `evillimiter.py:20-21` (`is_privileged()` → `os.geteuid() == 0`), enforced at `evillimiter.py:155-157`
- `install.sh` and `uninstall.sh` check `$(id -u) -ne 0`

## Install via curl (the only supported path)

```bash
curl -s https://raw.githubusercontent.com/XbibzOfficial777/evillimiter/master/install.sh | sudo bash
```

- Auto install script lives at `install.sh`
- Source is stored in hidden dir `/opt/.evillimiter` after install
- Standalone uninstaller at `uninstall.sh` (use if `--uninstall` flag is broken)

## PEP 668 trap (Ubuntu 24.04+)

- `pip install` is **blocked** system-wide. Two workarounds:
  1. `terminaltables` → install via `apt-get install python3-terminaltables` (NOT pip)
  2. All other deps → `pip3 install --break-system-packages`
- `install.sh` handles this; but any manual `pip install` will fail without `--break-system-packages`

## Dependencies

`requirements.txt` and `setup.py` `install_requires`:
- `colorama`, `netaddr`, `netifaces`, `tqdm`, `scapy` → pip
- `terminaltables` → apt (`python3-terminaltables`), **not** pip

## Package structure

```
evillimiter/
  __init__.py          # version
  evillimiter.py       # main entry: arg parsing, init, MainMenu launch
  console/
    banner.py          # ASCII art banner with "recoded by xbibz official"
    io.py              # IO class (colored print, style)
    shell.py           # shell command helper
    chart.py           # BarChart ASCII
    prompt.py          # PromptManager interactive prompt
  menus/
    main_menu.py       # MainMenu (834 lines) — the interactive UI loop
    menu.py            # CommandMenu base
    parser.py          # command parser
  networking/
    utils.py           # network resolution, cleanup, BitRate
    scan.py            # HostScanner (ARP scan)
    spoof.py           # ARPSpoofer
    limit.py           # Limiter (tc + iptables bandwidth throttle)
    monitor.py         # BandwidthMonitor
    host.py            # Host model
    watch.py           # HostWatcher reconnect detection
    flap.py            # Flapper — interface state management
  common/
    globals.py         # constants: BROADCAST, binary paths, sysctl key
```

## Architecture notes

- Uses `scapy` for ARP (spoofing + scan), `netifaces` for interface/gateway resolution
- Traffic shaping via `tc` + `iptables` — calls shell binaries (`evillimiter/console/shell.py`)
- Interactive CLI via `curses` + custom `PromptManager` (in `main_menu.py`)
- `--uninstall` flag does cleanup but **requires the module to import cleanly**; if deps are broken, use `uninstall.sh` instead
- `--cleanup` flag only resets network settings (iptables, tc, ip_forward)
- No docker, no venv, no Makefile, no tests

## Git notes

- Default branch: `master` (not `main`)
- Remote: `XbibzOfficial777/evillimiter`
- Tag: `evillimiter`
- Commit author: `XbibzOfficial777 <xbibzofficial@gmail.com>`
