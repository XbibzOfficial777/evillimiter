import enum
import collections

from evillimiter.console.io import IO


class CommandParser:
    class CommandType(enum.Enum):
        PARAMETER_COMMAND = 1
        FLAG_COMMAND = 2
        PARAMETERIZED_FLAG_COMMAND = 3

    FlagCommand = collections.namedtuple('FlagCommand', 'type, identifier, name')
    ParameterCommand = collections.namedtuple('ParameterCommand', 'type name optional')
    Subparser = collections.namedtuple('Subparser', 'identifier subparser handler')

    def __init__(self) -> None:
        self._flag_commands: list[collections.namedtuple] = []
        self._parameter_commands: list[collections.namedtuple] = []
        self._subparsers: list[collections.namedtuple] = []

    def add_parameter(self, name: str, optional: bool = False) -> None:
        command = CommandParser.ParameterCommand(
            type=CommandParser.CommandType.PARAMETER_COMMAND,
            name=name,
            optional=optional
        )
        self._parameter_commands.append(command)

    def add_flag(self, identifier: str, name: str) -> None:
        command = CommandParser.FlagCommand(
            type=CommandParser.CommandType.FLAG_COMMAND,
            identifier=identifier,
            name=name
        )
        self._flag_commands.append(command)

    def add_parameterized_flag(self, identifier: str, name: str) -> None:
        command = CommandParser.FlagCommand(
            type=CommandParser.CommandType.PARAMETERIZED_FLAG_COMMAND,
            identifier=identifier,
            name=name
        )
        self._flag_commands.append(command)

    def add_subparser(self, identifier: str, handler=None) -> 'CommandParser':
        subparser = CommandParser()
        command = CommandParser.Subparser(
            identifier=identifier,
            subparser=subparser,
            handler=handler
        )
        self._subparsers.append(command)
        return subparser

    def parse(self, command: list[str]) -> tuple | None:
        names = [x.name for x in (self._flag_commands + self._parameter_commands)]
        result_dict = dict.fromkeys(names, None)

        skip_next = False

        for i, arg in enumerate(command):
            if skip_next:
                skip_next = False
                continue

            if i == 0:
                for sp in self._subparsers:
                    if sp.identifier == arg:
                        result = sp.subparser.parse(command[(i + 1):])
                        if result is not None and sp.handler is not None:
                            sp.handler(result)
                        return result

            is_arg_processed = False

            for cmd in self._flag_commands:
                if cmd.identifier == arg:
                    if cmd.type == CommandParser.CommandType.FLAG_COMMAND:
                        result_dict[cmd.name] = True
                        is_arg_processed = True
                        break
                    elif cmd.type == CommandParser.CommandType.PARAMETERIZED_FLAG_COMMAND:
                        if (len(command) - 1) < (i + 1):
                            IO.error(f'parameter for flag {cmd.name} is missing')
                            return

                        value = command[i + 1]
                        result_dict[cmd.name] = value
                        skip_next = True
                        is_arg_processed = True
                        break

            if not is_arg_processed:
                for cmd in self._parameter_commands:
                    if result_dict[cmd.name] is None:
                        result_dict[cmd.name] = arg
                        is_arg_processed = True
                        break

            if not is_arg_processed:
                IO.error(f'{arg} is an unknown command.')
                return

        for cmd in self._parameter_commands:
            if result_dict[cmd.name] is None and not cmd.optional:
                IO.error(f'parameter {cmd.name} is missing')
                return

        for cmd in self._flag_commands:
            if cmd.type == CommandParser.CommandType.FLAG_COMMAND:
                if result_dict[cmd.name] is None:
                    result_dict[cmd.name] = False

        result_tuple = collections.namedtuple('ParseResult', list(result_dict.keys()))
        return result_tuple(**result_dict)