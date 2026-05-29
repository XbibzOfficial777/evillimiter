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
