import threading

import evillimiter.console.shell as shell
from .host import Host
from evillimiter.common.globals import BIN_TC, BIN_IPTABLES
from .utils import BitRate


class Limiter:
    class HostLimitIDs:
        def __init__(self, upload_id: int, download_id: int) -> None:
            self.upload_id = upload_id
            self.download_id = download_id

    def __init__(self, interface: str) -> None:
        self.interface = interface
        self._host_dict: dict = {}
        self._host_dict_lock = threading.Lock()

    def limit(self, host: Host, direction: 'Direction', rate: 'BitRate') -> None:
        host_ids = self._new_host_limit_ids(host, direction)
        burst = str(BitRate(int(rate.rate * 1.1)))

        if (direction & Direction.OUTGOING) == Direction.OUTGOING:
            ret = shell.execute_suppressed(f'{BIN_TC} class add dev {self.interface} parent 1:0 classid 1:{host_ids.upload_id} htb rate {rate} burst {burst}')
            if ret != 0:
                raise RuntimeError(f'failed to add tc upload class for {host.ip}')
            ret = shell.execute_suppressed(f'{BIN_TC} filter add dev {self.interface} parent 1:0 protocol ip prio {host_ids.upload_id} handle {host_ids.upload_id} fw flowid 1:{host_ids.upload_id}')
            if ret != 0:
                raise RuntimeError(f'failed to add tc upload filter for {host.ip}')
            ret = shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -A POSTROUTING -s {host.ip} -j MARK --set-mark {host_ids.upload_id}')
            if ret != 0:
                raise RuntimeError(f'failed to add iptables upload mark for {host.ip}')
        if (direction & Direction.INCOMING) == Direction.INCOMING:
            ret = shell.execute_suppressed(f'{BIN_TC} class add dev {self.interface} parent 1:0 classid 1:{host_ids.download_id} htb rate {rate} burst {burst}')
            if ret != 0:
                raise RuntimeError(f'failed to add tc download class for {host.ip}')
            ret = shell.execute_suppressed(f'{BIN_TC} filter add dev {self.interface} parent 1:0 protocol ip prio {host_ids.download_id} handle {host_ids.download_id} fw flowid 1:{host_ids.download_id}')
            if ret != 0:
                raise RuntimeError(f'failed to add tc download filter for {host.ip}')
            ret = shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -A PREROUTING -d {host.ip} -j MARK --set-mark {host_ids.download_id}')
            if ret != 0:
                raise RuntimeError(f'failed to add iptables download mark for {host.ip}')

        host.limited = True

        with self._host_dict_lock:
            self._host_dict[host] = {'ids': host_ids, 'rate': rate, 'direction': direction}

    def block(self, host: Host, direction: 'Direction') -> None:
        host_ids = self._new_host_limit_ids(host, direction)

        if (direction & Direction.OUTGOING) == Direction.OUTGOING:
            ret = shell.execute_suppressed(f'{BIN_IPTABLES} -I FORWARD 1 -s {host.ip} -j DROP')
            if ret != 0:
                raise RuntimeError(f'failed to add iptables forward drop for {host.ip}')
        if (direction & Direction.INCOMING) == Direction.INCOMING:
            ret = shell.execute_suppressed(f'{BIN_IPTABLES} -I FORWARD 1 -d {host.ip} -j DROP')
            if ret != 0:
                raise RuntimeError(f'failed to add iptables forward drop for {host.ip}')

        host.blocked = True

        with self._host_dict_lock:
            self._host_dict[host] = {'ids': host_ids, 'rate': None, 'direction': direction}

    def unlimit(self, host: Host, direction: 'Direction') -> None:
        if not host.limited and not host.blocked:
            return

        with self._host_dict_lock:
            host_ids = self._host_dict[host]['ids']

            if (direction & Direction.OUTGOING) == Direction.OUTGOING:
                self._delete_tc_class(host_ids.upload_id)
                self._delete_iptables_entries(host, direction, host_ids.upload_id)
            if (direction & Direction.INCOMING) == Direction.INCOMING:
                self._delete_tc_class(host_ids.download_id)
                self._delete_iptables_entries(host, direction, host_ids.download_id)

            del self._host_dict[host]

        host.limited = False
        host.blocked = False

    def replace(self, old_host: Host, new_host: Host) -> None:
        with self._host_dict_lock:
            info = self._host_dict.get(old_host)
        if info is not None:
            self.unlimit(old_host, Direction.BOTH)

            if info['rate'] is None:
                self.block(new_host, info['direction'])
            else:
                self.limit(new_host, info['direction'], info['rate'])

    def _new_host_limit_ids(self, host: Host, direction: 'Direction') -> 'Limiter.HostLimitIDs':
        with self._host_dict_lock:
            present = host in self._host_dict

        if present:
            self.unlimit(host, direction)

        return self.HostLimitIDs(*self._create_ids())

    def _create_ids(self) -> tuple[int, int]:
        with self._host_dict_lock:
            used_ids: set[int] = set()
            for info in self._host_dict.values():
                ids = info['ids']
                used_ids.add(ids.upload_id)
                used_ids.add(ids.download_id)

        id1 = 1
        while id1 in used_ids:
            id1 += 1

        id2 = id1 + 1
        while id2 in used_ids:
            id2 += 1

        return (id1, id2)

    def _delete_tc_class(self, id_: int) -> None:
        shell.execute_suppressed(f'{BIN_TC} filter del dev {self.interface} parent 1:0 prio {id_}')
        shell.execute_suppressed(f'{BIN_TC} class del dev {self.interface} parent 1:0 classid 1:{id_}')

    def _delete_iptables_entries(self, host: Host, direction: 'Direction', id_: int) -> None:
        if (direction & Direction.OUTGOING) == Direction.OUTGOING:
            shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -D POSTROUTING -s {host.ip} -j MARK --set-mark {id_}')
            shell.execute_suppressed(f'{BIN_IPTABLES} -t filter -D FORWARD -s {host.ip} -j DROP')
        if (direction & Direction.INCOMING) == Direction.INCOMING:
            shell.execute_suppressed(f'{BIN_IPTABLES} -t mangle -D PREROUTING -d {host.ip} -j MARK --set-mark {id_}')
            shell.execute_suppressed(f'{BIN_IPTABLES} -t filter -D FORWARD -d {host.ip} -j DROP')


class Direction:
    NONE = 0
    OUTGOING = 1
    INCOMING = 2
    BOTH = 3

    @staticmethod
    def pretty_direction(direction: int) -> str:
        if direction == Direction.OUTGOING:
            return 'upload'
        elif direction == Direction.INCOMING:
            return 'download'
        elif direction == Direction.BOTH:
            return 'upload / download'
        else:
            return '-'
