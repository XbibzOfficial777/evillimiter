import time
import threading


class HostWatcher:
    def __init__(self, host_scanner, reconnection_callback) -> None:
        self._scanner = host_scanner
        self._reconnection_callback = reconnection_callback
        self._hosts: set = set()
        self._hosts_lock = threading.Lock()

        self._interval = 45
        self._iprange = None
        self._settings_lock = threading.Lock()

        self._log_list: list = []
        self._log_list_lock = threading.Lock()

        self._running = False

    @property
    def interval(self) -> int:
        with self._settings_lock:
            return self._interval

    @interval.setter
    def interval(self, value: int) -> None:
        with self._settings_lock:
            self._interval = value

    @property
    def iprange(self):
        with self._settings_lock:
            return self._iprange

    @iprange.setter
    def iprange(self, value):
        with self._settings_lock:
            self._iprange = value

    @property
    def hosts(self) -> set:
        with self._hosts_lock:
            return self._hosts.copy()

    @property
    def log_list(self) -> list:
        with self._log_list_lock:
            return self._log_list.copy()

    def add(self, host) -> None:
        with self._hosts_lock:
            self._hosts.add(host)
        host.watched = True

    def remove(self, host) -> None:
        with self._hosts_lock:
            self._hosts.discard(host)
        host.watched = False

    def start(self) -> None:
        thread = threading.Thread(target=self._watch, daemon=True)
        self._running = True
        thread.start()

    def stop(self) -> None:
        self._running = False

    def _watch(self) -> None:
        while self._running:
            with self._hosts_lock:
                hosts = self._hosts.copy()

            if hosts:
                reconnected_hosts = self._scanner.scan_for_reconnects(hosts, self.iprange)
                for old_host, new_host in reconnected_hosts.items():
                    self._reconnection_callback(old_host, new_host)
                    with self._log_list_lock:
                        self._log_list.append({'old': old_host, 'new': new_host, 'time': time.strftime('%Y-%m-%d %H:%M')})

            time.sleep(self.interval)
