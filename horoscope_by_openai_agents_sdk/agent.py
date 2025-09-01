# ===========================
# main
# ===========================
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.run import RunConfig

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from tools import get_horoscope, get_lucky_item, get_zodiac_sign

# トレースを無効化
# set_tracing_disabled(True)

# ローカルトレースを有効化
from agents.tracing import set_trace_processors
from local_tracing import LocalJsonlAndPrettyProcessor
set_trace_processors([LocalJsonlAndPrettyProcessor()])


# -----------------------------
#  コンテキスト（ユーザー状態, session）
# -----------------------------
@dataclass
class UserContext:
    # TODO: 操作のツールが必要
    username: Optional[str] = None            # 例: "shohei"
    birthday: Optional[str] = None            # 例: "1990-04-12" (YYYY-MM-DD)
    zodiac:   Optional[str] = None            # 例: "Aries"
    # TODO: sessionの実装する
    # session: Dict[str, Any] = field(default_factory=dict)


# -----------------------------
#  Agent
# -----------------------------
class HoroscopeAgent:
    """占い機能を提供するエージェントクラス"""
    DEFAULT_BASE_URL = "http://localhost:1234/v1"
    DEFAULT_API_KEY = "not-needed"
    DEFAULT_MODEL = "openai/gpt-oss-20b"

    def __init__(self):
        self.user_input = None
        # TODO: 会話履歴の保存をAgents SDKの仕組みで実装する
        self.messages = []

        # modelにはlm-studioのgpt-oss-20bを指定
        self.gpt_oss_model = OpenAIChatCompletionsModel(
            model=self.DEFAULT_MODEL,
            openai_client=AsyncOpenAI(
                base_url=self.DEFAULT_BASE_URL,
                api_key=self.DEFAULT_API_KEY,
            ),
        )

        # Agentの初期化
        """
        name: エージェントを識別する必須の文字列。
        instructions: developer message または system prompt とも呼ばれます。
        model: 使用する LLM と、temperature、top_p などのモデル調整パラメーターを設定するオプションの model_settings。
        tools: エージェントがタスクを達成するために使用できるツール。
        """
        self.horoscope_agent = Agent[UserContext](
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

        # コンテキスト（最初は空）
        context = UserContext(
            username=None,
            birthday=None,
            zodiac=None,
        )

        # ユーザーメッセージを追加
        self.messages.append({"role": "user", "content": user_input})

        result = await Runner.run(
            self.horoscope_agent,
            input=self.messages,
            context=context,
            )
        
        # 保存
        self.messages.append({"role": "assistant", "content": result.final_output})

        return result.final_output