import difflib
from collections.abc import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory


class EvilLimiterCompleter(Completer):
    COMMANDS = [
        'scan', 'hosts', 'limit', 'block', 'free', 'add', 'monitor',
        'analyze', 'watch', 'clear', 'debug', 'quit', 'exit', 'help', '?',
        'flap', 'history', 'refresh', 'sort', 'select', 'selected', 'back',
    ]

    def __init__(self, get_hosts_fn: Callable | None = None) -> None:
        self._get_hosts = get_hosts_fn

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        if not text or text.isspace():
            return

        words = text.split()
        typing_word = not text.endswith(' ')
        current = document.get_word_before_cursor() if typing_word else ''

        if len(words) == 1 and typing_word:
            yield from self._command_completions(current)
            return

        first = words[0].lower()
        remaining = words[1:]

        if first == 'watch' and len(remaining) == 1 and typing_word:
            yield from self._static_completions(current, ('add', 'remove', 'set'))

        elif first in ('block', 'free', 'flap', 'analyze', 'limit') and self._get_hosts:
            yield from self._id_completions(current, typing_word)

        elif first == 'sort' and len(remaining) <= 1:
            yield from self._static_completions(current, ('ip', 'name', 'id', 'status', 'mac'))

    def _command_completions(self, current: str):
        for cmd in self.COMMANDS:
            if cmd.startswith(current) and cmd != current:
                yield Completion(cmd, start_position=-len(current))
        if len(current) >= 2:
            for match in difflib.get_close_matches(current, self.COMMANDS, n=3, cutoff=0.5):
                if match != current:
                    yield Completion(match, start_position=-len(current))

    def _static_completions(self, current, options):
        if not current:
            for opt in options:
                yield Completion(opt, start_position=0)
        else:
            for opt in options:
                if opt.startswith(current):
                    yield Completion(opt, start_position=-len(current))

    def _id_completions(self, current, typing_word):
        if not typing_word:
            yield Completion('all', start_position=0)
            return
        if 'all'.startswith(current):
            yield Completion('all', start_position=-len(current))
        hosts = self._get_hosts()
        if hosts:
            host_list = list(hosts) if not isinstance(hosts, list) else hosts
            for i, host in enumerate(host_list):
                hid = str(i)
                if hid.startswith(current):
                    yield Completion(hid, start_position=-len(current))


class PromptManager:
    def __init__(self, get_hosts_fn: Callable | None = None) -> None:
        self.history_store: list[str] = []
        self._history = InMemoryHistory()
        self._completer = EvilLimiterCompleter(get_hosts_fn)
        self._session = PromptSession(
            history=self._history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=self._completer,
            complete_while_typing=True,
            complete_in_thread=True,
        )

    def prompt(self, ansi_prompt: str) -> str:
        cmd = self._session.prompt(ANSI(ansi_prompt))
        if cmd.strip():
            self.history_store.append(cmd.strip())
        return cmd
