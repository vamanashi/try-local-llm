# ===========================
# main
# ===========================
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, ItemHelpers, Runner, set_tracing_disabled
from agents.run import RunConfig
import os

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from tools import get_horoscope, get_lucky_item, get_zodiac_sign
from history import AgentHistory

# トレースを無効化
set_tracing_disabled(True)

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

    def __init__(self, history_jsonl_path: Optional[str] = None):
        self.user_input = None
        # TODO: 会話履歴の保存をAgents SDKの仕組みで実装する
        self.messages = []
        # エージェントの履歴（出力ログ）
        self.history = AgentHistory()
        # 履歴の保存先（逐次保存を Agent 側で制御）
        module_dir = os.path.dirname(__file__)
        default_jsonl = os.path.join(module_dir, "logs", "session_history.jsonl")
        self._history_jsonl_path = history_jsonl_path or default_jsonl

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

        # コンテキスト（セッション間で保持したいユーザー状態）
        self.context = UserContext(
            username=None,
            birthday=None,
            zodiac=None,
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

        # ユーザーメッセージを追加（Agents SDK 入力）
        self.messages.append({"role": "user", "content": user_input})
        # 履歴にもユーザー入力を記録・逐次保存（JSONLのみ）
        self.history.add_user_input(user_input)
        self.history.persist_last(jsonl_path=self._history_jsonl_path)

        # これまでの会話（ユーザー/アシスタント両方）をそのまま入力として渡す
        # Agents SDK は list[TResponseInputItem] 形式を受け付ける
        result = Runner.run_streamed(
            self.horoscope_agent,
            input=self.messages,
            context=self.context,
        )
        
        assistant_texts: List[str] = []
        async for event in result.stream_events():
            # エージェント履歴クラスに処理を委譲（最小改修）
            formatted = self.history.handle_event(event)
            if formatted is not None:
                yield formatted
                # 逐次で永続化（JSONL のみ）
                self.history.persist_last(jsonl_path=self._history_jsonl_path)
                # アシスタント出力は次ターン以降の文脈に追加
                if getattr(event, "type", None) == "run_item_stream_event":
                    item = getattr(event, "item", None)
                    if getattr(item, "type", None) == "message_output_item":
                        try:
                            text = ItemHelpers.text_message_output(item)
                        except Exception:
                            text = None
                        if text:
                            assistant_texts.append(text)

        # ランの終了後、今回のアシスタント応答を会話履歴にまとめて追加
        if assistant_texts:
            self.messages.append({"role": "assistant", "content": "\n".join(assistant_texts)})
