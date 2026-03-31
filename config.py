import os
from dotenv import load_dotenv
from prompt_toolkit.styles import Style

load_dotenv(".env")

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")

MODEL_NAME = os.getenv("MODEL_NAME", "GLM-4.7-Flash")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.5"))



STYLE = Style.from_dict(
    {
        "prompt.brand": "bold #6C63FF",
        "prompt.dim": "#666666",
        "prompt.symbol": "bold #00A36C",
        "toolbar": "bg:#1f2335 #f0f0f0",
        "output.info": "#4B5563",
        "output.ok": "#00A36C",
        "output.warn": "#E67E22",
    }
)