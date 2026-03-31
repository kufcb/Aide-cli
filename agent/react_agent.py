from typing import Annotated, Sequence,TypedDict
import json
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage,ToolMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from tools.file_tool import *
from tools.terminal_tool import *
from chat.zhipu_chat import model as llm
from logs.logging_server import logger

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


tools = [write_to_file, read_file, run_terminal_command]
tools_by_name = {tool.name: tool for tool in tools}
logger.info(f"现在有的工具:{tools_by_name}")
model = llm.bind_tools(tools)
system_prompt = SystemMessage(content="你是一个 AI 助手。如果需要,你可以使用工具来获取信息来构建你的答案。")

def call_model(state: AgentState):
    response = model.invoke(state["messages"])
    ai_messages = [response]
    return {"messages": ai_messages}


def tool_node(state: AgentState):
    logger.info("开始调用工具")
    outputs = []
    last_message = state["messages"][-1]
    if (hasattr(last_message, "tool_calls") and last_message.tool_calls):
        # 遍历每个工具调用
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            logger.info(f"调用工具: {tool_name},参数: {tool_args}")

            # 根据工具名称找到对应的工具函数并执行
            if tool_name in tools_by_name:
                result = tools_by_name[tool_name].invoke(tool_args)
            else:
                result = f"工具 '{tool_name}' 不存在"
            # 将结果包装为 ToolMessage
            # ToolMessage 会被 LLM 读取，作为 Observation（观察结果）
            outputs.append(
                ToolMessage(
                    content=json.dumps(
                        result, ensure_ascii=False
                    ),  # 工具结果转为 JSON 字符串
                    name=tool_name,
                    tool_call_id=tool_call.get("id"),  # 关联对应的 tool_call
                )
            )
    logger.info(f"调用结果: {outputs}")
    return {"messages": outputs}



def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]

    # 检查是否有工具调用请求
    if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
        # 没有工具调用，任务完成
        return "end"
    else:
        # 有工具调用，需要执行工具后继续
        return "continue"


graph_builder = StateGraph(AgentState)
# 添加节点
graph_builder.add_node("call_model", call_model)  # LLM 推理节点
graph_builder.add_node("tool_node", tool_node)  # 工具执行节点

# 设置入口点：从 START 进入 call_model
graph_builder.set_entry_point("call_model")

# 添加普通边：tool_node 执行完后，回到 call_model 继续推理
graph_builder.add_edge("tool_node", "call_model")


# 添加条件边：从 call_model 出发，根据 should_continue 的结果决定去向
graph_builder.add_conditional_edges(
    "call_model",
    should_continue,
    {
        "continue": "tool_node",  # 继续循环：去执行工具
        "end": END,  # 结束循环：任务完成
    },
)

# 编译图，生成可执行的工作流
graph = graph_builder.compile()

def agent_run(
        user_input:str
):
    inputs = {
        "messages": [HumanMessage(content=user_input)],
    }
    for event in graph.stream(inputs, stream_mode="values"):
        messages = event.get("messages", [])
        if messages:
            last_message = messages[-1]
            logger.info(f"最新消息: {last_message}")
            msg_type = getattr(last_message, "type", "unknown")
            content = getattr(last_message, "content", "")
            if msg_type == "ai":
                # AI 回复
                tool_calls = getattr(last_message, "tool_calls", None)
                if tool_calls:
                    tool_names = [tc.get("name", "unknown") for tc in tool_calls]
                    print(f"正在思考... 调用工具中")
                else:
                    print(f"答案是:{content}")

            elif msg_type == "tool":
                result = json.loads(content)
                print(f"工具获取结果: {result}")
            elif msg_type == "human":
                pass
