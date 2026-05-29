import argparse
import collections
import json
import os
import platform
import re
import shutil
import subprocess
import time
import urllib.request
import urllib.error

import netaddr
import evillimiter.networking.utils as netutils
from evillimiter import __version__, __description__
from evillimiter.common import config as ev_config
from evillimiter.menus.main_menu import MainMenu
from evillimiter.console.banner import get_main_banner
from evillimiter.console.io import IO
from evillimiter.networking.scan import HostScanner
from evillimiter.networking.spoof import ARPSpoofer, NDPSpoofer
from evillimiter.networking.limit import Limiter, Direction
from evillimiter.networking.monitor import BandwidthMonitor
from evillimiter.networking.utils import BitRate

REPO_API = 'https://api.github.com/repos/XbibzOfficial777/evillimiter/releases/latest'
CACHE_FILE = '/opt/.evillimiter/.update_cache'
CACHE_TTL = 86400  # 1 day in seconds


InitialArguments = collections.namedtuple('InitialArguments', 'interface, gateway_ip, netmask, gateway_mac')


def is_privileged() -> bool:
    return os.geteuid() == 0


def is_linux() -> bool:
    return platform.system() == 'Linux'


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f'{__description__}.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    net_group = parser.add_argument_group('Network settings')
    net_group.add_argument('-i', '--interface', help='network interface connected to the target network. automatically resolved if not specified.')
    net_group.add_argument('-g', '--gateway-ip', dest='gateway_ip', help='default gateway ip address. automatically resolved if not specified.')
    net_group.add_argument('-m', '--gateway-mac', dest='gateway_mac', help='gateway mac address. automatically resolved if not specified.')
    net_group.add_argument('-n', '--netmask', help='netmask for the network. automatically resolved if not specified.')

    action_group = parser.add_argument_group('Actions')
    action_group.add_argument('-f', '--flush', action='store_true', help='flush current iptables (firewall) and tc (traffic control) settings.')
    action_group.add_argument('-c', '--cleanup', action='store_true', help='clean up all iptables rules, tc qdiscs, and disable IP forwarding.')

    other_group = parser.add_argument_group('Other')
    other_group.add_argument('--colorless', action='store_true', help='disable colored output.')
    other_group.add_argument('-v', '--version', action='version', version=f'evillimiter {__version__}')
    other_group.add_argument('--uninstall', action='store_true', help='completely remove evillimiter and all its files.')
    other_group.add_argument('--sniffer', action='store_true', help='sniffer mode: monitor without spoofing.')

    nonint_group = parser.add_argument_group('Non-interactive (scripting)')
    nonint_group.add_argument('--limit-ip', metavar='IP', help='limit bandwidth for an IP (requires --rate).')
    nonint_group.add_argument('--block-ip', metavar='IP', help='block internet for an IP.')
    nonint_group.add_argument('--unblock-ip', metavar='IP', help='unblock/unlimit an IP.')
    nonint_group.add_argument('--rate', metavar='RATE', help='rate for --limit-ip (e.g. 500kbit, 1mbit).')
    nonint_group.add_argument('--direction', choices=['upload', 'download', 'both'], default='both', help='traffic direction (default: both).')

    return parser.parse_args()


def process_arguments(args: argparse.Namespace) -> InitialArguments | None:
    if args.interface is None:
        interface = netutils.get_default_interface()
        if interface is None:
            IO.error('default interface could not be resolved. specify manually (-i).')
            return None
    else:
        interface = args.interface
        if not netutils.exists_interface(interface):
            IO.error(f'interface {IO.Fore.LIGHTYELLOW_EX}{interface}{IO.Style.RESET_ALL} does not exist.')
            return None

    IO.ok(f'interface: {IO.Fore.LIGHTYELLOW_EX}{interface}{IO.Style.RESET_ALL}')

    if args.gateway_ip is None:
        gateway_ip = netutils.get_default_gateway()
        if gateway_ip is None:
            IO.error('default gateway address could not be resolved. specify manually (-g).')
            return None
    else:
        gateway_ip = args.gateway_ip

    IO.ok(f'gateway ip: {IO.Fore.LIGHTYELLOW_EX}{gateway_ip}{IO.Style.RESET_ALL}')

    if args.gateway_mac is None:
        gateway_mac = netutils.get_mac_by_ip(interface, gateway_ip)
        if gateway_mac is None:
            IO.error('gateway mac address could not be resolved.')
            return None
    else:
        if netutils.validate_mac_address(args.gateway_mac):
            gateway_mac = args.gateway_mac.lower()
        else:
            IO.error('gateway mac is invalid.')
            return None

    IO.ok(f'gateway mac: {IO.Fore.LIGHTYELLOW_EX}{gateway_mac}{IO.Style.RESET_ALL}')

    if args.netmask is None:
        netmask = netutils.get_default_netmask(interface)
        if netmask is None:
            IO.error('netmask could not be resolved. specify manually (-n).')
            return None
    else:
        netmask = args.netmask

    IO.ok(f'netmask: {IO.Fore.LIGHTYELLOW_EX}{netmask}{IO.Style.RESET_ALL}')

    if args.flush:
        netutils.flush_network_settings(interface)
        IO.spacer()
        IO.ok('flushed network settings')

    return InitialArguments(interface=interface, gateway_ip=gateway_ip, gateway_mac=gateway_mac, netmask=netmask)


def initialize(interface: str) -> bool:
    if not netutils.create_qdisc_root(interface):
        IO.spacer()
        IO.error('qdisc root handle could not be created. maybe flush network settings (--flush).')
        return False

    if not netutils.enable_ip_forwarding():
        IO.spacer()
        IO.error('ip forwarding could not be enabled.')
        return False

    return True


def cleanup(interface: str) -> None:
    netutils.delete_qdisc_root(interface)
    netutils.disable_ip_forwarding()


def _non_interactive(args, init_args) -> None:
    if not initialize(init_args.interface):
        return

    iprange = list(netaddr.IPNetwork(f'{init_args.gateway_ip}/{init_args.netmask}'))
    scanner = HostScanner(init_args.interface, iprange)
    hosts = scanner.scan()

    if not hosts:
        IO.error('no hosts discovered.')
        cleanup(init_args.interface)
        return

    target = None
    for h in hosts:
        if h.ip == getattr(args, 'limit_ip') or h.ip == getattr(args, 'block_ip') or h.ip == getattr(args, 'unblock_ip'):
            target = h
            break

    if target is None:
        IO.error(f'IP not found in scan results.')
        cleanup(init_args.interface)
        return

    arp_spoofer = ARPSpoofer(init_args.interface, init_args.gateway_ip, init_args.gateway_mac)
    limiter = Limiter(init_args.interface)
    monitor = BandwidthMonitor(init_args.interface, 1)

    arp_spoofer.start()
    monitor.start()

    direction = Direction.BOTH
    if args.direction == 'upload':
        direction = Direction.OUTGOING
    elif args.direction == 'download':
        direction = Direction.INCOMING

    if args.limit_ip:
        if not args.rate:
            IO.error('--rate is required for --limit-ip.')
            cleanup(init_args.interface)
            return
        try:
            rate = BitRate.from_rate_string(args.rate)
        except Exception:
            IO.error('invalid rate format.')
            cleanup(init_args.interface)
            return
        arp_spoofer.add(target)
        limiter.limit(target, direction, rate)
        monitor.add(target)
        IO.ok(f'{target.ip} limited to {rate} ({args.direction}).')
        IO.print(f'Press Ctrl+C to stop limiting and exit.')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    elif args.block_ip:
        arp_spoofer.add(target)
        limiter.block(target, direction)
        monitor.add(target)
        IO.ok(f'{target.ip} blocked ({args.direction}).')
        IO.print(f'Press Ctrl+C to unblock and exit.')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    elif args.unblock_ip:
        if target.spoofed:
            arp_spoofer.remove(target)
        limiter.unlimit(target, Direction.BOTH)
        monitor.remove(target)
        IO.ok(f'{target.ip} freed.')

    arp_spoofer.stop()
    monitor.stop()
    cleanup(init_args.interface)


def _print_startup_info(version: str, interface: str, gateway_ip: str, gateway_mac: str, netmask: str) -> None:
    header = f'{IO.Style.BRIGHT}evillimiter v{version}{IO.Style.RESET_ALL}'
    info_lines = [
        f' {header}',
        f' Interface:  {IO.Fore.LIGHTYELLOW_EX}{interface}{IO.Style.RESET_ALL}',
        f' Gateway:    {IO.Fore.LIGHTYELLOW_EX}{gateway_ip}{IO.Style.RESET_ALL}',
        f' Netmask:    {IO.Fore.LIGHTYELLOW_EX}{netmask}{IO.Style.RESET_ALL}',
    ]
    stripped = [IO._remove_colors(l) for l in info_lines]
    width = max(len(s) for s in stripped) + 2
    border = '─' * width
    IO.print(f'┌{border}┐')
    for line, stripped_line in zip(info_lines, stripped):
        IO.print(f'│{line}{" " * (width - len(stripped_line))}│')
    IO.print(f'└{border}┘')


def check_for_update() -> str | None:
    # check cache first
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                cached = f.read().strip()
            ts_str, ver = cached.split('|', 1)
            if time.time() - float(ts_str) < CACHE_TTL:
                return ver if ver else None
        except (ValueError, OSError):
            pass

    try:
        req = urllib.request.Request(REPO_API, headers={'User-Agent': 'evillimiter', 'Accept': 'application/vnd.github+json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        latest_tag = data.get('tag_name', '')
        m = re.search(r'(\d+\.\d+\.\d+)', latest_tag)
        latest = m.group(1) if m else ''
        result = latest if (latest and latest != __version__) else ''
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, OSError):
        result = ''

    # write cache
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            f.write(f'{time.time()}|{result}')
    except OSError:
        pass

    return result if result else None


def run() -> None:
    version = __version__
    cfg = ev_config.load_config()
    args = parse_arguments()

    IO.initialize(args.colorless)
    IO.print(get_main_banner(version))

    update = check_for_update()
    if update:
        IO.spacer()
        IO.print(f'[{IO.Fore.LIGHTYELLOW_EX}*{IO.Style.RESET_ALL}] Update available: v{__version__} -> v{update}')
        IO.print(f'  curl -s https://raw.githubusercontent.com/XbibzOfficial777/evillimiter/master/install.sh | sudo bash')
        IO.spacer()

    if not is_linux():
        IO.error('run under linux.')
        return

    if not is_privileged():
        IO.error('run as root.')
        return

    if args.uninstall:
        IO.print(f'[{IO.Fore.LIGHTYELLOW_EX}*{IO.Style.RESET_ALL}] Uninstalling evillimiter...')
        IO.spacer()

        IO.print(f'  [{IO.Fore.LIGHTYELLOW_EX}>{IO.Style.RESET_ALL}] Cleaning network settings...')
        netutils.cleanup_all()

        IO.print(f'  [{IO.Fore.LIGHTYELLOW_EX}>{IO.Style.RESET_ALL}] Removing package...')
        subprocess.run(['pip3', 'uninstall', 'evillimiter', '-y'], capture_output=True)
        subprocess.run(['pip3', 'uninstall', 'evillimiter', '-y'], capture_output=True)

        IO.print(f'  [{IO.Fore.LIGHTYELLOW_EX}>{IO.Style.RESET_ALL}] Removing binary...')
        for path in ['/usr/local/bin/evillimiter', '/usr/bin/evillimiter']:
            if os.path.exists(path):
                os.remove(path)

        IO.print(f'  [{IO.Fore.LIGHTYELLOW_EX}>{IO.Style.RESET_ALL}] Removing hidden source directory...')
        shutil.rmtree('/opt/.evillimiter', ignore_errors=True)

        IO.print(f'  [{IO.Fore.LIGHTYELLOW_EX}>{IO.Style.RESET_ALL}] Removing cache files...')
        shutil.rmtree('/tmp/.evillimiter-install', ignore_errors=True)
        IO.spacer()
        IO.ok('evillimiter has been completely uninstalled.')
        IO.print(f'[{IO.Fore.LIGHTRED_EX}!{IO.Style.RESET_ALL}] Recoded by Xbibz Official')
        return

    if args.cleanup:
        netutils.cleanup_all()
        IO.spacer()
        IO.ok('Network settings cleaned up.')
        return

    init_args = process_arguments(args)

    if init_args is None:
        return

    # Non-interactive mode
    if args.limit_ip or args.block_ip or args.unblock_ip:
        _non_interactive(args, init_args)
        return

    if args.sniffer:
        cfg['sniffer_mode'] = True

    if not initialize(init_args.interface):
        return

    gateway_ipv6 = netutils.get_default_gateway_ipv6(init_args.interface)
    if gateway_ipv6:
        IO.ok(f'gateway ipv6: {IO.Fore.LIGHTYELLOW_EX}{gateway_ipv6}{IO.Style.RESET_ALL}')

    IO.spacer()
    _print_startup_info(version, init_args.interface, init_args.gateway_ip, init_args.gateway_mac, init_args.netmask)

    IO.print('Auto-scanning network...')
    iprange = list(netaddr.IPNetwork(f'{init_args.gateway_ip}/{init_args.netmask}'))
    scanner = HostScanner(init_args.interface, iprange)
    hosts = scanner.scan()
    IO.spacer()

    if len(hosts) == 0:
        IO.error('No hosts discovered during auto-scan.')
        IO.ok('Continuing with empty host list. Use "scan" command to scan manually.')
    else:
        IO.ok(f'{len(hosts)} hosts discovered.')

    ndp_spoofer = NDPSpoofer(init_args.interface, init_args.gateway_mac, gateway_ipv6) if gateway_ipv6 else None

    IO.spacer()
    menu = MainMenu(version, init_args.interface, init_args.gateway_ip, init_args.gateway_mac, init_args.netmask, initial_hosts=hosts, ndp_spoofer=ndp_spoofer, config=cfg)
    menu.start()
    cleanup(init_args.interface)


if __name__ == '__main__':
    run()
