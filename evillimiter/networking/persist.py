import json
import os

from .host import Host
from .limit import Direction
from .utils import BitRate

LIMITS_PATH = '/opt/.evillimiter/limits.json'


def save_limits(host_dict: dict) -> None:
    data = {}
    for host, info in host_dict.items():
        data[host.mac] = {
            'ip': host.ip,
            'ipv6': host.ipv6,
            'rate': str(info.get('rate')) if info.get('rate') else None,
            'blocked': host.blocked,
            'limited': host.limited,
            'direction': info.get('direction', Direction.BOTH),
        }
    os.makedirs(os.path.dirname(LIMITS_PATH), exist_ok=True)
    with open(LIMITS_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def load_limits() -> dict:
    if not os.path.exists(LIMITS_PATH):
        return {}
    try:
        with open(LIMITS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def clear_limits() -> None:
    if os.path.exists(LIMITS_PATH):
        os.remove(LIMITS_PATH)


def reapply_limits(hosts: list[Host], limiter, arp_spoofer, bandwidth_monitor, ndp_spoofer=None) -> int:
    saved = load_limits()
    count = 0
    for host in hosts:
        entry = saved.get(host.mac)
        if entry is None:
            continue
        direction = entry.get('direction', Direction.BOTH)
        arp_spoofer.add(host)
        if ndp_spoofer and host.ipv6:
            ndp_spoofer.add(host)
        bandwidth_monitor.add(host)
        if entry.get('blocked'):
            limiter.block(host, direction)
        elif entry.get('limited') and entry.get('rate'):
            try:
                rate = BitRate.from_rate_string(entry['rate'])
                limiter.limit(host, direction, rate)
            except Exception:
                pass
        count += 1
    return count
