import os
from dotenv import load_dotenv
from prompt_toolkit.styles import Style

load_dotenv(".env")


def _get_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default

    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")

MODEL_NAME = os.getenv("MODEL_NAME", "GLM-4.7-Flash")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.5"))
TERMINAL_COMMAND_CONFIRM_ENABLED = _get_bool_env(
    "TERMINAL_COMMAND_CONFIRM_ENABLED",
    True,
)



STYLE = Style.from_dict(
    {
        "prompt.brand": "bold #6C63FF",
        "prompt.dim": "#666666",
        "prompt.symbol": "bold #00A36C",
        "toolbar": "bg:#1f2335 #f0f0f0",
        "output.info": "#4B5563",
        "output.ok": "#00A36C",
        "output.warn": "#E67E22",
        "welcome.border": "#6B7280",
        "welcome.title": "bold #0F172A",
        "welcome.subtitle": "#374151",
        "welcome.section": "bold #0EA5E9",
        "welcome.body": "#111827",
        "welcome.art": "bold #D97706",
    }
)
