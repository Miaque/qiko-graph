from typing import Literal

from configs import qiko_configs
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode
from state import State


@tool
def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")


tools = [get_weather]


model = ChatOpenAI(
    temperature=0, api_key=qiko_configs.ONE_API_KEY, base_url=qiko_configs.ONE_API_URL, model="glm-4-plus"
).bind_tools(tools)

llm = ChatOpenAI(
    temperature=0, api_key=qiko_configs.ONE_API_KEY, base_url=qiko_configs.ONE_API_URL, model="glm-4-plus"
).with_config(tags=["final_node"])


def should_continue(state: State) -> Literal["tools", "final"]:
    messages = state["messages"]
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we stop (reply to the user)
    return "final"


async def call_model(state: State, config: RunnableConfig):
    messages = state["messages"]
    response = await model.ainvoke(messages, config)
    return {"messages": [response]}


async def call_final_model(state: State):
    messages = state["messages"]
    last_ai_message = messages[-1]
    response = await llm.ainvoke(
        [
            SystemMessage("Rewrite this in the voice of Al Roker and output in Chinese."),
            HumanMessage(last_ai_message.content),
        ]
    )
    # overwrite the last AI message from the agent
    response.id = last_ai_message.id
    return {"messages": [response]}


graph_builder = StateGraph(State)
graph_builder.add_node("agent", call_model)
graph_builder.add_node("tools", ToolNode(tools))
graph_builder.add_node("final", call_final_model)

graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges("agent", should_continue, ["tools", "final"])
graph_builder.add_edge("tools", "agent")

memory = MemorySaver()
graph = graph_builder.compile()
