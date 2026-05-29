from evillimiter.console.io import IO


class Host:
    def __init__(self, ip: str, mac: str, name: str, ipv6: list[str] | None = None) -> None:
        self.ip = ip
        self.mac = mac
        self.name = name
        self.ipv6 = ipv6 if ipv6 is not None else []
        self.spoofed = False
        self.limited = False
        self.blocked = False
        self.watched = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Host):
            return NotImplemented
        return self.ip == other.ip or (self.mac == other.mac and self.mac != '00:00:00:00:00:00')

    def __hash__(self) -> int:
        return hash((self.mac, self.ip))

    def __repr__(self) -> str:
        ipv6_str = ', '.join(self.ipv6) if self.ipv6 else ''
        return f"Host(ip='{self.ip}', mac='{self.mac}', name='{self.name}', ipv6=[{ipv6_str}])"

    def pretty_status(self) -> str:
        if self.limited:
            return f"{IO.Fore.LIGHTRED_EX}Limited{IO.Style.RESET_ALL}"
        elif self.blocked:
            return f"{IO.Fore.RED}Blocked{IO.Style.RESET_ALL}"
        else:
            return 'Free'
