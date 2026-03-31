import os
from dotenv import load_dotenv

load_dotenv(".env")

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")

MODEL_NAME = os.getenv("MODEL_NAME", "GLM-4.7-Flash")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.5"))