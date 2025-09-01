# ===========================
# main
# ===========================

from openai import OpenAI
import json
import tools
from logger import log_action

class HoroscopeAgent:
    """占い機能を提供するエージェントクラス"""
    DEFAULT_BASE_URL = "http://localhost:1234/v1"
    DEFAULT_API_KEY = "not-needed"
    DEFAULT_MODEL = "openai/gpt-oss-20b"

    def __init__(self):
        self.client = OpenAI(base_url=self.DEFAULT_BASE_URL, api_key=self.DEFAULT_API_KEY)
        self.user_input = None
        self.messages = []

    def _load_instructions(self, filepath="instruction.txt"):
        """指示文をファイルから読み込む"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                instructions = f.read()
            self.messages.append({"role": "system", "content": instructions})
        except Exception as e:
            print("指示文の読み込みエラー:", e)

    @log_action
    def _call_llm(self, messages):
        """LLMを呼び出す共通処理"""
        try:
            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                tools=tools.tools,
                messages=messages,
                )
            return response
        except Exception as e:
            print("LLM呼び出しエラー:", e)
            return None
    
    @log_action
    def _call_tool(self, tool_call):
        """ツールを呼び出す共通処理"""
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments or "{}")
        if hasattr(tools, tool_name):
            try:
                func = getattr(tools, tool_name)
                result = func(**arguments)
                return result
            except Exception as e:
                print(f"ツール呼び出しエラー ({tool_name}):", e)
                return None
        else:
            raise ValueError(f"Function {tool_name} not found in tools module")

    @log_action
    def run(self, user_input):
        """
        システムメッセージ + 渡された履歴でLLM呼び出し
        ツール呼び出しがあれば1回だけ実行して結果を返す
        複数回のツール呼び出しが必要な場合は、チャット側で再度runを呼び出す
        """

        # 初回のみ指示文を読み込む
        if not self.messages:
            self._load_instructions()

        # メッセージの準備
        # messagesをworking（run実行中に用いる会話履歴）にコピーして、ユーザーメッセージを追加
        working = self.messages.copy()
        working.append({"role": "user", "content": user_input})

        # LLMの応答をもとにアクションを決める
        # ツールの呼び出しがあれば実行して結果を返す、ツールの呼び出しがなければループを終了して応答を返す
        while True:
            # todo: 回数を制限したほうがよいかも

            # LLM呼び出し
            response = self._call_llm(working)

            # 応答メッセージを追加
            msg = response.choices[0].message
            working.append({
                "role": "assistant", 
                "content": msg.content or "", 
                "tool_calls": msg.tool_calls
                })
            
            # ツール呼び出しがなければループを抜ける
            if not msg.tool_calls:
                break

            # ツール呼び出しがあれば実行して結果を返す
            for tc in msg.tool_calls:
                result = self._call_tool(tc)
                # ツールの実行結果をメッセージに追加
                working.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps({"horoscope": result}, ensure_ascii=False),
                })

        # 今回のrun実行による会話履歴（working）を保存
        self.messages = working

        # 最終応答メッセージを返却
        return msg.content

