from ddgs import DDGS
from langchain_core.tools import tool

@tool
def duckduckgo_search(query: str) -> str:
    """联网搜索，获取实时信息、最新数据、外部知识。"""
    try:
        # 获取前5条搜索结果
        results = DDGS().text(query, max_results=5)
        # 格式化返回给LLM
        return "\n\n".join([
            f"【{res['title']}】\n{res['body']}\n来源: {res['href']}"
            for res in results
        ])
    except Exception as e:
        return f"搜索出错: {e}"



__all__ = ["duckduckgo_search"]