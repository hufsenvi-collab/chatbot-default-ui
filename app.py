import asyncio
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env")

PYTHON_EXECUTABLE = Path(sys.executable)
REAL_ESTATE_MCP_EXECUTABLE = PYTHON_EXECUTABLE.with_name(
    "korea-realestate-mcp.exe" if os.name == "nt" else "korea-realestate-mcp"
)

MCP_SERVERS = {
    "demo": {
        "command": str(PYTHON_EXECUTABLE),
        "args": [str(APP_DIR / "server.py")],
        "transport": "stdio",
    },
    "korea-realestate": {
        "command": str(REAL_ESTATE_MCP_EXECUTABLE),
        "args": [],
        "transport": "stdio",
        "env": {
            "PUBLIC_DATA_API_KEY": "3875e566dbd423f1f3962c615644990d1070f99aa1d093c3bffd183ec7d5f4de",
        },
    },
}


async def run_agent(prompt: str) -> str:
    if not os.getenv("PUBLIC_DATA_API_KEY"):
        raise RuntimeError(
            "PUBLIC_DATA_API_KEY가 없습니다. .env 파일에 공공데이터포털 서비스 키를 설정하세요."
        )
    if not REAL_ESTATE_MCP_EXECUTABLE.is_file():
        raise RuntimeError(
            "korea-realestate-mcp가 현재 Python 환경에 설치되어 있지 않습니다. "
            "requirements.txt를 설치한 뒤 다시 실행하세요."
        )

    client = MultiServerMCPClient(MCP_SERVERS)
    tools = await client.get_tools()
    agent = create_agent("gpt-5.4-mini", tools)
    response = await agent.ainvoke({"messages": prompt})
    return response["messages"][-1].content


st.title("실습 에이전트")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("무엇을 알려드릴까요?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("답변을 준비하고 있습니다..."):
            try:
                result = asyncio.run(run_agent(prompt))
            except Exception as exc:
                result = f"요청을 처리하지 못했습니다: {exc}"
        st.markdown(result)

    st.session_state.messages.append({"role": "assistant", "content": result})
