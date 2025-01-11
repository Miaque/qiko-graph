import json
import logging
import os
import sys
import time
import uuid
from typing import List, Optional

from configs import qiko_configs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from graph import llm
from langchain_core.runnables import RunnableConfig
from my_socket.main import socket_app
from pydantic import BaseModel, Field
from subgraph import graph

os.environ["TZ"] = "Asia/Shanghai"
if hasattr(time, "tzset"):
    time.tzset()

logging.basicConfig(
    level=qiko_configs.LOG_LEVEL,
    format=qiko_configs.LOG_FORMAT,
    datefmt=qiko_configs.LOG_DATEFORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
log_tz = qiko_configs.LOG_TZ

if log_tz:
    from datetime import datetime

    import pytz

    timezone = pytz.timezone(log_tz)

    def time_converter(seconds):
        return datetime.utcfromtimestamp(seconds).astimezone(timezone).timetuple()

    for handler in logging.root.handlers:
        handler.formatter.converter = time_converter

logger = logging.getLogger(__name__)


config = {
    "configurable": {
        # The passenger_id is used in our flight tools to
        # fetch the user's flight information
        "passenger_id": "3442 587242",
        # Checkpoints are accessed by thread_id
        "thread_id": str(uuid.uuid4()),
    }
}


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    question: Question
    answer: str


def inp(question: str):
    return {"messages": [("user", question)]}


def out(result):
    return result


app = FastAPI(docs_url="/docs", openapi_url="/openapi.json")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 Socket.IO 应用到 /ws 路径
app.mount("/ws", socket_app)


class InputPayload(BaseModel):
    input: dict


class MetadataPayload(BaseModel):
    langgraph_node: Optional[str] = None


class ResponsePayload(BaseModel):
    event: str
    name: str
    run_id: str
    metadata: MetadataPayload
    parent_ids: List[str] = Field(default_factory=list)


@app.post("/generate")
async def generate(p: InputPayload):
    async def response_stream():
        try:
            async for event in graph.astream_events(
                p.input, config=RunnableConfig(configurable=config["configurable"]), version="v2"
            ):
                # print(event)
                kind = event["event"]
                tags = event.get("tags", [])

                # yield f"data: {event}\n\n"

                yield f"data: {ResponsePayload(**event)}\n\n"

                # if kind == "on_chat_model_stream" and event["metadata"].get("langgraph_node") == "agent":
                #     content = event["data"]["chunk"].content
                #     yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

                # if event["event"] == "on_chat_model_stream" and event["metadata"].get("langgraph_node") == "final":
                #     content = event["data"]["chunk"].content
                #     yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

                # if event["event"] == "on_chat_model_stream" and "final_node" in tags:
                #     content = event["data"]["chunk"].content
                #     yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception(e)

    return StreamingResponse(response_stream(), media_type="text/event-stream")


@app.post("/stream")
async def stream(question: Question):
    async def response_stream():
        async for event in llm.astream_events(question.question, version="v2"):
            kind = event["event"]
            event_data = event["data"]
            logger.info(f"{kind} ==> {event_data}")
            if "chunk" in event_data:
                chunk = event_data["chunk"]
                yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(response_stream(), media_type="text/event-stream")
