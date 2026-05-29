import re
import warnings
import netifaces
from scapy.all import ARP, sr1

import evillimiter.console.shell as shell
from evillimiter.common.globals import BIN_TC, BIN_IPTABLES, BIN_IP6TABLES, BIN_SYSCTL, IP_FORWARD_LOC, IP6_FORWARD_LOC


def get_default_interface() -> str | None:
    gateways = netifaces.gateways()
    if 'default' in gateways and netifaces.AF_INET in gateways['default']:
        return gateways['default'][netifaces.AF_INET][1]


def get_default_gateway() -> str | None:
    gateways = netifaces.gateways()
    if 'default' in gateways and netifaces.AF_INET in gateways['default']:
        return gateways['default'][netifaces.AF_INET][0]


def get_default_gateway_ipv6(interface: str) -> str | None:
    out = shell.output_suppressed(f'ip -6 route show default dev {interface} 2>/dev/null | head -1 | awk \'{{print $3}}\'')
    return out.strip() or None


def get_default_netmask(interface: str) -> str | None:
    ifaddrs = netifaces.ifaddresses(interface)
    if netifaces.AF_INET in ifaddrs:
        return ifaddrs[netifaces.AF_INET][0].get('netmask')


def get_default_prefixlen_ipv6(interface: str) -> str | None:
    ifaddrs = netifaces.ifaddresses(interface)
    if netifaces.AF_INET6 in ifaddrs:
        for addr in ifaddrs[netifaces.AF_INET6]:
            if not addr['addr'].startswith('fe80'):
                return addr.get('netmask')
    if netifaces.AF_INET6 in ifaddrs:
        return ifaddrs[netifaces.AF_INET6][0].get('netmask')
    return None


def get_mac_by_ip(interface: str, address: str) -> str | None:
    packet = ARP(op=1, pdst=address)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        response = sr1(packet, timeout=3, verbose=0, iface=interface)

    if response is not None:
        return response.hwsrc


def get_mac_by_ipv6(interface: str, address: str) -> str | None:
    shell.execute_suppressed(f'ping6 -c 1 -W 1 -I {interface} {address} 2>/dev/null')
    out = shell.output_suppressed(f'ip -6 neigh get {address} dev {interface} 2>/dev/null')
    if 'lladdr' in out:
        parts = out.split()
        for i, p in enumerate(parts):
            if p == 'lladdr' and i + 1 < len(parts):
                return parts[i + 1].lower()
    return None


def get_ndp_cache(interface: str) -> dict[str, str]:
    result: dict[str, str] = {}
    out = shell.output_suppressed(f'ip -6 neigh show dev {interface} 2>/dev/null')
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[1] == 'lladdr':
            ip = parts[0].lower()
            mac = parts[2].lower()
            result[ip] = mac
    return result


def exists_interface(interface: str) -> bool:
    return interface in netifaces.interfaces()


def flush_network_settings(interface: str) -> None:
    shell.execute_suppressed(f'{BIN_IPTABLES} -P INPUT ACCEPT')
    shell.execute_suppressed(f'{BIN_IPTABLES} -P OUTPUT ACCEPT')
    shell.execute_suppressed(f'{BIN_IPTABLES} -P FORWARD ACCEPT')

    shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -F')
    shell.execute_suppressed(f'{BIN_IPTABLES} -t nat -F')
    shell.execute_suppressed(f'{BIN_IPTABLES} -F')
    shell.execute_suppressed(f'{BIN_IPTABLES} -X')

    shell.execute_suppressed(f'{BIN_IP6TABLES} -t mangle -F')
    shell.execute_suppressed(f'{BIN_IP6TABLES} -F')

    shell.execute_suppressed(f'{BIN_TC} qdisc del dev {interface} root')


def validate_ip_address(ip: str) -> bool:
    match = re.match(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$', ip)
    if not match:
        return False
    return all(0 <= int(octet) <= 255 for octet in match.groups())


def validate_ipv6_address(ip: str) -> bool:
    try:
        import ipaddress
        ipaddress.IPv6Address(ip)
        return True
    except ValueError:
        return False


def validate_mac_address(mac: str) -> bool:
    return re.match(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$', mac) is not None


def create_qdisc_root(interface: str) -> bool:
    return shell.execute_suppressed(f'{BIN_TC} qdisc add dev {interface} root handle 1:0 htb') == 0


def delete_qdisc_root(interface: str) -> int:
    return shell.execute_suppressed(f'{BIN_TC} qdisc del dev {interface} root handle 1:0 htb')


def enable_ip_forwarding() -> bool:
    ok = shell.execute_suppressed(f'{BIN_SYSCTL} -w {IP_FORWARD_LOC}=1') == 0
    shell.execute_suppressed(f'{BIN_SYSCTL} -w {IP6_FORWARD_LOC}=1')
    return ok


def disable_ip_forwarding() -> bool:
    ok = shell.execute_suppressed(f'{BIN_SYSCTL} -w {IP_FORWARD_LOC}=0') == 0
    shell.execute_suppressed(f'{BIN_SYSCTL} -w {IP6_FORWARD_LOC}=0')
    return ok


def cleanup_all() -> None:
    for iface in netifaces.interfaces():
        if iface == 'lo':
            continue
        shell.execute_suppressed(f'{BIN_TC} qdisc del dev {iface} root')

    shell.execute_suppressed(f'{BIN_IPTABLES} -P INPUT ACCEPT')
    shell.execute_suppressed(f'{BIN_IPTABLES} -P OUTPUT ACCEPT')
    shell.execute_suppressed(f'{BIN_IPTABLES} -P FORWARD ACCEPT')
    shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -F')
    shell.execute_suppressed(f'{BIN_IPTABLES} -t nat -F')
    shell.execute_suppressed(f'{BIN_IPTABLES} -F')
    shell.execute_suppressed(f'{BIN_IPTABLES} -X')

    shell.execute_suppressed(f'{BIN_IP6TABLES} -t mangle -F')
    shell.execute_suppressed(f'{BIN_IP6TABLES} -F')

    shell.execute_suppressed(f'{BIN_SYSCTL} -w {IP_FORWARD_LOC}=0')
    shell.execute_suppressed(f'{BIN_SYSCTL} -w {IP6_FORWARD_LOC}=0')


class ValueConverter:
    @staticmethod
    def byte_to_bit(v: int) -> int:
        return v * 8


class BitRate:
    def __init__(self, rate: int = 0) -> None:
        self.rate = rate

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        counter = 0
        r = self.rate

        while True:
            if r >= 1000:
                r /= 1000
                counter += 1
            else:
                unit = ''
                if counter == 0:
                    unit = 'bit'
                elif counter == 1:
                    unit = 'kbit'
                elif counter == 2:
                    unit = 'mbit'
                elif counter == 3:
                    unit = 'gbit'

                return f'{int(r)}{unit}'

            if counter > 3:
                raise Exception('Bitrate limit exceeded')

    def __mul__(self, other: object) -> 'BitRate':
        if isinstance(other, BitRate):
            return BitRate(int(self.rate * other.rate))
        return BitRate(int(self.rate * other))

    def fmt(self, fmt: str) -> str:
        string = self.__str__()
        end = len([c for c in string if c.isdigit()])
        num = int(string[:end])

        return f'{fmt % num}{string[end:]}'

    @classmethod
    def from_rate_string(cls, rate_string: str) -> 'BitRate':
        return cls(BitRate._bit_value(rate_string))

    @staticmethod
    def _bit_value(rate_string: str) -> int:
        number = 0
        offset = 0

        for c in rate_string:
            if c.isdigit():
                number = number * 10 + int(c)
                offset += 1
            else:
                break

        unit = rate_string[offset:].lower()

        if unit == 'bit':
            return number
        elif unit == 'kbit':
            return number * 1000
        elif unit == 'mbit':
            return number * 1000 ** 2
        elif unit == 'gbit':
            return number * 1000 ** 3
        else:
            raise Exception('Invalid bitrate')


class ByteValue:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        counter = 0
        v = self.value

        while True:
            if v >= 1024:
                v /= 1024
                counter += 1
            else:
                unit = ''
                if counter == 0:
                    unit = 'b'
                elif counter == 1:
                    unit = 'kb'
                elif counter == 2:
                    unit = 'mb'
                elif counter == 3:
                    unit = 'gb'
                elif counter == 4:
                    unit = 'tb'

                return f'{int(v)}{unit}'

            if counter > 3:
                raise Exception('Byte value limit exceeded')

    def __int__(self) -> int:
        return self.value

    def __add__(self, other: object) -> 'ByteValue':
        if isinstance(other, ByteValue):
            return ByteValue(int(self.value + other.value))
        return ByteValue(int(self.value + other))

    def __sub__(self, other: object) -> 'ByteValue':
        if isinstance(other, ByteValue):
            return ByteValue(int(self.value - other.value))
        return ByteValue(int(self.value - other))

    def __mul__(self, other: object) -> 'ByteValue':
        if isinstance(other, ByteValue):
            return ByteValue(int(self.value * other.value))
        return ByteValue(int(self.value * other))

    def __ge__(self, other: object) -> bool:
        if isinstance(other, ByteValue):
            return self.value >= other.value
        return self.value >= other

    def fmt(self, fmt: str) -> str:
        string = self.__str__()
        end = len([c for c in string if c.isdigit()])
        num = int(string[:end])

        return f'{fmt % num}{string[end:]}'

    @classmethod
    def from_byte_string(cls, byte_string: str) -> 'ByteValue':
        return cls(ByteValue._byte_value(byte_string))

    @staticmethod
    def _byte_value(byte_string: str) -> int:
        number = 0
        offset = 0

        for c in byte_string:
            if c.isdigit():
                number = number * 10 + int(c)
                offset += 1
            else:
                break

        unit = byte_string[offset:].lower()

        if unit == 'b':
            return number
        elif unit == 'kb':
            return number * 1024
        elif unit == 'mb':
            return number * 1024 ** 2
        elif unit == 'gb':
            return number * 1024 ** 3
        elif unit == 'tb':
            return number * 1024 ** 4
        else:
            raise Exception('Invalid byte string')
