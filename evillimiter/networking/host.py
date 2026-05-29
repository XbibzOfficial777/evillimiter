from evillimiter.console.io import IO


class Host:
    def __init__(self, ip: str, mac: str, name: str) -> None:
        self.ip = ip
        self.mac = mac
        self.name = name
        self.spoofed = False
        self.limited = False
        self.blocked = False
        self.watched = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Host):
            return NotImplemented
        return self.ip == other.ip

    def __hash__(self) -> int:
        return hash((self.mac, self.ip))

    def __repr__(self) -> str:
        return f"Host(ip='{self.ip}', mac='{self.mac}', name='{self.name}')"

    def pretty_status(self) -> str:
        if self.limited:
            return f"{IO.Fore.LIGHTRED_EX}Limited{IO.Style.RESET_ALL}"
        elif self.blocked:
            return f"{IO.Fore.RED}Blocked{IO.Style.RESET_ALL}"
        else:
            return 'Free'
