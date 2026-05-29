import sys
import socket
import warnings
import logging
from tqdm import tqdm
from netaddr import IPAddress
from scapy.all import sr1, ARP
from scapy.config import conf as scapy_conf
from concurrent.futures import ThreadPoolExecutor

scapy_conf.log_level = logging.ERROR

from .host import Host
from evillimiter.console.io import IO
import evillimiter.console.shell as shell


class HostScanner:
    def __init__(self, interface: str, iprange: list, ipv6_range: str | None = None) -> None:
        self.interface = interface
        self.iprange = iprange
        self.ipv6_range = ipv6_range

        self.max_workers = 75
        self.retries = 0
        self.timeout = 2.5

        self._resolve_names = True
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def scan(self, iprange=None) -> list[Host]:
        ipv4_range = [str(x) for x in (self.iprange if iprange is None else iprange)]
        hosts = []

        # IPv4 ARP scan
        iterator = tqdm(
            iterable=self._executor.map(self._sweep, ipv4_range),
            total=len(ipv4_range),
            ncols=45,
            bar_format='{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt}'
        )

        try:
            for host in iterator:
                if host is not None:
                    try:
                        host_info = socket.gethostbyaddr(host.ip)
                        name = '' if host_info is None else host_info[0]
                        host.name = name
                    except socket.herror:
                        pass
                    hosts.append(host)
        except KeyboardInterrupt:
            iterator.close()
            IO.ok('aborted. waiting for shutdown...')

        # IPv6 NDP scan
        ipv6_hosts = self._scan_ipv6(ipv4_range)
        self._merge_ipv6_hosts(hosts, ipv6_hosts)

        return hosts

    def _scan_ipv6(self, ipv4_range: list[str]) -> list[Host]:
        ipv6_hosts: list[Host] = []

        # Probe via multicast ping to populate NDP cache
        shell.execute_suppressed(f'ping -c 1 -W 1 -I {self.interface} ff02::1 2>/dev/null')
        shell.execute_suppressed(f'ping6 -c 1 -W 1 -I {self.interface} ff02::1 2>/dev/null')

        # Read NDP cache
        ndp = self._get_ndp_cache()
        for ipv6_addr, mac in ndp.items():
            ipv6_hosts.append(Host(ipv6_addr, mac, '', ipv6=[ipv6_addr]))

        return ipv6_hosts

    def _get_ndp_cache(self) -> dict[str, str]:
        result: dict[str, str] = {}
        out = shell.output_safe(f'ip -6 neigh show dev {self.interface}')
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[1] == 'lladdr':
                ip = parts[0].lower()
                if ip.startswith('fe80'):
                    continue
                mac = parts[2].lower()
                if mac != '00:00:00:00:00:00':
                    result[ip] = mac
        return result

    def _merge_ipv6_hosts(self, hosts: list[Host], ipv6_hosts: list[Host]) -> None:
        mac_to_host = {h.mac: h for h in hosts if h.mac != '00:00:00:00:00:00'}
        for v6host in ipv6_hosts:
            ipv6_addr = v6host.ip
            mac = v6host.mac
            if mac in mac_to_host:
                existing = mac_to_host[mac]
                if ipv6_addr not in existing.ipv6:
                    existing.ipv6.append(ipv6_addr)
            else:
                hosts.append(Host('', mac, '', ipv6=[ipv6_addr]))

    def scan_for_reconnects(self, hosts, iprange=None) -> dict:
        scanned_hosts = []
        ipv4_range = [str(x) for x in (self.iprange if iprange is None else iprange)]

        try:
            for host in self._executor.map(self._sweep, ipv4_range):
                if host is not None:
                    scanned_hosts.append(host)
        except KeyboardInterrupt:
            return {}

        # Also scan IPv6 for reconnect
        ipv6_scanned = self._scan_ipv6(ipv4_range)
        self._merge_ipv6_hosts(scanned_hosts, ipv6_scanned)

        reconnected_hosts = {}
        for host in hosts:
            for s_host in scanned_hosts:
                if host.mac == s_host.mac and host.ip != s_host.ip:
                    s_host.name = host.name
                    reconnected_hosts[host] = s_host

        return reconnected_hosts

    def _sweep(self, ip: str):
        packet = ARP(op=1, pdst=ip)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            answer = sr1(packet, retry=self.retries, timeout=self.timeout, verbose=0, iface=self.interface)

        if answer is not None:
            return Host(ip, answer.hwsrc, '')
