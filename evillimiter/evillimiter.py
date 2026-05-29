import argparse
import collections
import os
import platform

import netaddr
import evillimiter.networking.utils as netutils
from evillimiter import __version__, __description__
from evillimiter.menus.main_menu import MainMenu
from evillimiter.console.banner import get_main_banner
from evillimiter.console.io import IO
from evillimiter.networking.scan import HostScanner


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


def run() -> None:
    version = __version__
    args = parse_arguments()

    IO.initialize(args.colorless)
    IO.print(get_main_banner(version))

    if not is_linux():
        IO.error('run under linux.')
        return

    if not is_privileged():
        IO.error('run as root.')
        return

    if args.cleanup:
        netutils.cleanup_all()
        IO.spacer()
        IO.ok('Network settings cleaned up.')
        return

    init_args = process_arguments(args)

    if init_args is None:
        return

    if not initialize(init_args.interface):
        return

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

    IO.spacer()
    menu = MainMenu(version, init_args.interface, init_args.gateway_ip, init_args.gateway_mac, init_args.netmask, initial_hosts=hosts)
    menu.start()
    cleanup(init_args.interface)


if __name__ == '__main__':
    run()
