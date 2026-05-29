import json
import os

CONFIG_PATH = '/opt/.evillimiter/config.json'

DEFAULT_CONFIG = {
    'default_rate': '1mbit',
    'default_direction': 'both',
    'sniffer_mode': False,
    'autosave_limits': True,
}

def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                user = json.load(f)
            cfg.update(user)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg

def save_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=2)
