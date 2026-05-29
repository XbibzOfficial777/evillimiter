import os
import subprocess


DEVNULL = open(os.devnull, 'w')


def execute(command: str, root: bool = True) -> int:
    return subprocess.call(command, shell=True)


def execute_suppressed(command: str, root: bool = True) -> int:
    return subprocess.call(command, shell=True, stdout=DEVNULL, stderr=DEVNULL)


def output(command: str, root: bool = True) -> str:
    return subprocess.check_output(command, shell=True).decode('utf-8')


def output_suppressed(command: str, root: bool = True) -> str:
    return subprocess.check_output(command, shell=True, stderr=DEVNULL).decode('utf-8')


def output_safe(command: str, root: bool = True) -> str:
    try:
        return subprocess.check_output(command, shell=True, stderr=DEVNULL).decode('utf-8')
    except subprocess.CalledProcessError:
        return ''


def locate_bin(name: str) -> str:
    try:
        return output_suppressed(f'which {name}').replace('\n', '')
    except subprocess.CalledProcessError:
        raise FileNotFoundError(f'missing util: {name}, check your PATH')
