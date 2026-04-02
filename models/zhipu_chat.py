import os
from config import ZHIPUAI_API_KEY,MODEL_NAME, MODEL_TEMPERATURE
from langchain_community.chat_models import ChatZhipuAI

os.environ["ZHIPUAI_API_KEY"] = ZHIPUAI_API_KEY

model = ChatZhipuAI(
    model=MODEL_NAME,
    temperature=MODEL_TEMPERATURE,
)
