import time
import threading
from scapy.sendrecv import sniff
from scapy.layers.inet import IP
from scapy.layers.inet6 import IPv6

from .utils import ValueConverter, BitRate, ByteValue


class BandwidthMonitor:
    class BandwidthMonitorResult:
        def __init__(self) -> None:
            self.upload_rate = BitRate()
            self.upload_total_size = ByteValue()
            self.upload_total_count = 0
            self.download_rate = BitRate()
            self.download_total_size = ByteValue()
            self.download_total_count = 0

            self._upload_temp_size = ByteValue()
            self._download_temp_size = ByteValue()

    def __init__(self, interface: str, interval: int) -> None:
        self.interface = interface

        self._host_result_dict: dict = {}
        self._host_result_lock = threading.Lock()

        self._running = False

        self._promiscuous_data: dict[str, int] = {}
        self._promiscuous_sent: dict[str, int] = {}
        self._promiscuous_received: dict[str, int] = {}
        self._promiscuous_lock = threading.Lock()

    def add(self, host) -> None:
        with self._host_result_lock:
            if host not in self._host_result_dict:
                self._host_result_dict[host] = {'result': BandwidthMonitor.BandwidthMonitorResult(), 'last_now': time.time()}

    def remove(self, host) -> None:
        with self._host_result_lock:
            self._host_result_dict.pop(host, None)

    def replace(self, old_host, new_host) -> None:
        with self._host_result_lock:
            if old_host in self._host_result_dict:
                self._host_result_dict[new_host] = self._host_result_dict[old_host]
                del self._host_result_dict[old_host]

    def start(self) -> None:
        if self._running:
            return

        sniff_thread = threading.Thread(target=self._sniff, daemon=True)
        sniff_thread.start()

        self._running = True

    def stop(self) -> None:
        self._running = False

    def get(self, host):
        with self._host_result_lock:
            if host in self._host_result_dict:
                last_now = self._host_result_dict[host]['last_now']
                time_passed = time.time() - last_now
                result = self._host_result_dict[host]['result']
                result.upload_rate = BitRate(int(ValueConverter.byte_to_bit(result._upload_temp_size.value) / time_passed))
                result.download_rate = BitRate(int(ValueConverter.byte_to_bit(result._download_temp_size.value) / time_passed))

                result._upload_temp_size *= 0
                result._download_temp_size *= 0

                self._host_result_dict[host]['last_now'] = time.time()
                return result

    def _sniff(self) -> None:
        def pkt_handler(pkt):
            addrs = self._extract_addrs(pkt)
            if addrs is None:
                return
            src, dst = addrs
            with self._host_result_lock:
                for host in self._host_result_dict:
                    result = self._host_result_dict[host]['result']
                    if src in (host.ip, *host.ipv6):
                        result.upload_total_size += len(pkt)
                        result.upload_total_count += 1
                        result._upload_temp_size += len(pkt)
                    elif dst in (host.ip, *host.ipv6):
                        result.download_total_size += len(pkt)
                        result.download_total_count += 1
                        result._download_temp_size += len(pkt)

        sniff(iface=self.interface, prn=pkt_handler, stop_filter=lambda pkt: not self._running, store=0)

    @staticmethod
    def _extract_addrs(pkt):
        if pkt.haslayer(IP):
            return (pkt[IP].src, pkt[IP].dst)
        if pkt.haslayer(IPv6):
            return (pkt[IPv6].src, pkt[IPv6].dst)
        return None

    def start_promiscuous(self, duration: int = 0) -> dict:
        with self._promiscuous_lock:
            self._promiscuous_data.clear()
            self._promiscuous_sent.clear()
            self._promiscuous_received.clear()

        def pkt_handler(pkt):
            addrs = self._extract_addrs(pkt)
            if addrs is None:
                return
            src, dst = addrs
            pkt_len = len(pkt)
            with self._promiscuous_lock:
                self._promiscuous_sent[src] = self._promiscuous_sent.get(src, 0) + pkt_len
                self._promiscuous_received[dst] = self._promiscuous_received.get(dst, 0) + pkt_len
                self._promiscuous_data[src] = self._promiscuous_data.get(src, 0) + pkt_len
                self._promiscuous_data[dst] = self._promiscuous_data.get(dst, 0) + pkt_len

        if duration == 0:
            t = threading.Thread(target=lambda: sniff(iface=self.interface, prn=pkt_handler, store=0), daemon=True)
            t.start()
            return dict(self._promiscuous_data)
        else:
            sniff(iface=self.interface, prn=pkt_handler, store=0, timeout=duration)
            return dict(self._promiscuous_data)

    def get_promiscuous_summary(self, top_n: int = 10) -> list[tuple[str, int, str]]:
        result = []
        with self._promiscuous_lock:
            for ip, bytes_sent in self._promiscuous_sent.items():
                result.append((ip, bytes_sent, 'sent'))
            for ip, bytes_recv in self._promiscuous_received.items():
                result.append((ip, bytes_recv, 'received'))
        result.sort(key=lambda x: x[1], reverse=True)
        return result[:top_n]