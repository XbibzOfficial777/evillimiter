import enum
import collections

from .parser import CommandParser
from evillimiter.console.io import IO


class CommandMenu:
    def __init__(self) -> None:
        self.prompt = '>>> '
        self.parser = CommandParser()
        self._active = False

    def argument_handler(self, args: tuple) -> None:
        pass

    def interrupt_handler(self) -> None:
        self.stop()

    def start(self) -> None:
        self._active = True

        while self._active:
            try:
                command = IO.input(self.prompt)
            except KeyboardInterrupt:
                self.interrupt_handler()
                break

            parsed_args = self.parser.parse(command.split())
            if parsed_args is not None:
                self.argument_handler(parsed_args)

    def stop(self) -> None:
        self._active = False
