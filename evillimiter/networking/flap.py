import threading

from .host import Host
from .limit import Limiter, Direction


class Flapper:
    def __init__(self, limiter: Limiter) -> None:
        self._limiter = limiter
        self._flapping: dict[Host, threading.Event] = {}
        self._flap_lock = threading.Lock()

    def start(self, host: Host, block_time: int = 2, free_time: int = 2) -> None:
        with self._flap_lock:
            if host in self._flapping:
                self._stop(host)

            stop_event = threading.Event()
            self._flapping[host] = stop_event

        thread = threading.Thread(
            target=self._cycle,
            args=(host, block_time, free_time, stop_event),
            daemon=True
        )
        thread.start()

    def stop(self, host: Host) -> None:
        with self._flap_lock:
            self._stop(host)

    def stop_all(self) -> None:
        with self._flap_lock:
            for host in list(self._flapping.keys()):
                self._stop(host)

    def is_flapping(self, host: Host) -> bool:
        with self._flap_lock:
            return host in self._flapping

    def _stop(self, host: Host) -> None:
        if host in self._flapping:
            self._flapping[host].set()
            del self._flapping[host]

    def _cycle(self, host: Host, block_time: int, free_time: int, stop_event: threading.Event) -> None:
        try:
            while not stop_event.is_set():
                self._limiter.block(host, Direction.BOTH)
                if stop_event.wait(block_time):
                    return
                self._limiter.unlimit(host, Direction.BOTH)
                stop_event.wait(free_time)
        finally:
            self._limiter.unlimit(host, Direction.BOTH)
