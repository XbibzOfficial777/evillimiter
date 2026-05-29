from evillimiter.console.io import IO


class BarChart:
    def __init__(self, draw_char: str = '▇', max_bar_length: int = 30) -> None:
        self.draw_char = draw_char
        self.max_bar_length = max_bar_length
        self._data: list[dict] = []

    def add_value(self, value: int, prefix: str, suffix: str = '') -> None:
        self._data.append({'value': value, 'prefix': prefix, 'suffix': suffix})

    def get(self, reverse: bool = False) -> str:
        def _remap(
            n: float, old_min: float, old_max: float, new_min: float, new_max: float
        ) -> float:
            return (((n - old_min) * (new_max - new_min)) / (old_max - old_min)) + new_min

        self._data.sort(reverse=reverse, key=lambda x: x['value'])

        max_value = self._data[0]['value'] if reverse else self._data[-1]['value']
        max_prefix_length = max(len(item['prefix']) for item in self._data) + 1

        chart = ''

        for item in self._data:
            if max_value == 0:
                bar_length = 0
            else:
                bar_length = round(_remap(item['value'], 0, max_value, 0, self.max_bar_length))

            chart += (
                f"{item['prefix']}{' ' * (max_prefix_length - len(item['prefix']))}: "
                f"{self.draw_char * bar_length} {item['suffix']}\n"
            )

        return chart[:-1]


class LiveGraph:
    def __init__(self, max_bars: int = 20, bar_char: str = '█', empty_char: str = '░') -> None:
        self.max_bars = max_bars
        self.bar_char = bar_char
        self.empty_char = empty_char
        self._history: dict[str, list[int]] = {}

    def add_sample(self, host_id: str, upload_rate: int, download_rate: int) -> None:
        if host_id not in self._history:
            self._history[host_id] = [upload_rate, download_rate]
        else:
            self._history[host_id].append(upload_rate)
            self._history[host_id].append(download_rate)
            if len(self._history[host_id]) > self.max_bars * 2:
                self._history[host_id] = self._history[host_id][-(self.max_bars * 2):]

    @staticmethod
    def format_rate(bits_per_sec: int) -> str:
        if bits_per_sec >= 1_000_000:
            return f'{bits_per_sec / 1_000_000:.1f} Mbit'
        elif bits_per_sec >= 1_000:
            return f'{bits_per_sec / 1_000:.0f} Kbit'
        return f'{bits_per_sec} bit'

    def _rate_bars(self, rate: int, max_rate: int, bar_length: int) -> str:
        if max_rate == 0:
            filled = 0
        else:
            filled = int(round(rate / max_rate * bar_length))
        filled = min(filled, bar_length)
        empty = bar_length - filled
        return self.bar_char * filled + self.empty_char * empty

    def render(self) -> str:
        lines = []
        max_rate = 0
        for host_id, history in self._history.items():
            if len(history) >= 2:
                up = history[-2]
                dn = history[-1]
                max_rate = max(max_rate, up, dn)

        bar_length = self.max_bars

        for host_id, history in self._history.items():
            if len(history) >= 2:
                up = history[-2]
                dn = history[-1]
                up_str = self._rate_bars(up, max_rate, bar_length)
                dn_str = self._rate_bars(dn, max_rate, bar_length)
                up_label = self.format_rate(up)
                dn_label = self.format_rate(dn)
                lines.append(f'{IO.Style.BRIGHT}[{host_id}]{IO.Style.RESET_ALL}')
                lines.append(
                    f'  {IO.Fore.LIGHTGREEN_EX}UP:{IO.Style.RESET_ALL}  '
                    f'{up_str} {up_label}'
                )
                lines.append(
                    f'  {IO.Fore.LIGHTRED_EX}DN:{IO.Style.RESET_ALL}  '
                    f'{dn_str} {dn_label}'
                )

        return '\n'.join(lines)

    def clear(self) -> None:
        self._history.clear()
