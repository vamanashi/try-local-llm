# ===========================
# main
# ===========================
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, ItemHelpers, Runner, set_tracing_disabled
import os

import json
from typing import Optional, List
from tools import get_horoscope, get_lucky_item, get_zodiac_sign
from session import JSONLSession

# トレースを無効化
set_tracing_disabled(True)

# -----------------------------
#  Agent
# -----------------------------
class HoroscopeAgent:
    """占い機能を提供するエージェントクラス"""
    DEFAULT_BASE_URL = "http://localhost:1234/v1"
    DEFAULT_API_KEY = "not-needed"
    DEFAULT_MODEL = "openai/gpt-oss-20b"

    def __init__(self, session_id: Optional[str] = None):
        # 会話履歴の管理は SDK セッションへ移行
        self.session = JSONLSession(session_id or "default")
        module_dir = os.path.dirname(__file__)

        # modelにはlm-studioのgpt-oss-20bを指定
        self.gpt_oss_model = OpenAIChatCompletionsModel(
            model=self.DEFAULT_MODEL,
            openai_client=AsyncOpenAI(
                base_url=self.DEFAULT_BASE_URL,
                api_key=self.DEFAULT_API_KEY,
            ),
        )

        # Agentの初期化
        self.horoscope_agent = Agent(
            name="Horoscope Agent",
            instructions=self._load_instructions("instruction.txt"),
            model=self.gpt_oss_model,
            tools=[get_horoscope, get_lucky_item, get_zodiac_sign],
        )

    def _load_instructions(self, filepath):
        """指示文をファイルから読み込む"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                instructions = f.read()
            return instructions
        except Exception as e:
            print("指示文の読み込みエラー:", e)

    async def run(self, user_input):

        result = Runner.run_streamed(
            self.horoscope_agent,
            input=user_input,
            session=self.session,
        )
        
        assistant_texts: List[str] = []
        async for event in result.stream_events():
            # We'll ignore the raw responses event deltas
            if event.type == "raw_response_event":
                continue
            # When the agent updates, print that
            elif event.type == "agent_updated_stream_event":
                yield f"Agent updated: {event.new_agent.name}\n"
                continue
            # When items are generated, print them
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    yield f"Agent({event.item.agent.name}): tooled: {event.item.raw_item.name}, with args: {event.item.raw_item.arguments}\n"
                elif event.item.type == "tool_call_output_item":
                    yield f"Agent({event.item.agent.name}): tool output: {event.item.output}\n"
                elif event.item.type == "message_output_item":
                    yield f"Agent({event.item.agent.name}): Message output:\n {ItemHelpers.text_message_output(event.item)}\n"
                else:
                    pass  # Ignore other event types