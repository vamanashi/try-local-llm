from openai import OpenAI
import json

# ===========================
# utils
# ===========================

def save_log(obj, message=None):
    """リクエストまたはレスポンスを指定ファイルに保存"""
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- start: {message} ---\n")
        
        # OpenAIオブジェクトをdictに変換
        if hasattr(obj, "model_dump"):
            obj = obj.model_dump()
        
        # リストや辞書の中のOpenAIオブジェクトも変換
        obj = convert_to_serializable(obj)
        
        # JSON型ではない場合はそのまま書き込む
        if not isinstance(obj, (dict, list)):
            f.write(str(obj) + "\n")
        else:
            # dictまたはlistの場合はjsonとして保存
            json.dump(obj, f, ensure_ascii=False, indent=2)
        
        f.write(f"\n--- end ---\n")

def convert_to_serializable(obj):
    """オブジェクトをJSON化可能な形に再帰的に変換"""
    if obj is None:
        return None
    elif hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj

# ===========================
# main
# ===========================

# client = OpenAI()
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

# 1. モデル用の呼び出し可能なツールのリストを定義
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_horoscope",
            "description": "占星術のサインの今日の運勢を取得します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sign": {
                        "type": "string",
                        "description": "牡牛座や水瓶座などの占星術のサイン",
                    }
                },
                "required": ["sign"],
            },
        },
    }
]

def get_horoscope(sign):
    return f"{sign}: 来週の火曜日にあなたは赤ちゃんのカワウソと友達になるでしょう。"

# 時間をかけて追加していく実行中の入力リストを作成
messages = [
    {"role": "user", "content": "私の運勢はどうですか？私は水瓶座です。"}
]

# 2. 定義されたツールでモデルにプロンプトを送信
save_log(messages, "ユーザーの最初のメッセージ")
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    tools=tools,
    messages=messages,
)
save_log(response.model_dump(), "モデルの最初の応答")

msg = response.choices[0].message
messages.append({
    "role": "assistant", 
    "content": msg.content or "", 
    "tool_calls": msg.tool_calls
    })

# ツール呼び出しがあれば実行して結果を返す
if msg.tool_calls:
    for tc in msg.tool_calls:
        if tc.function.name == "get_horoscope":
            args = json.loads(tc.function.arguments or "{}")
            result = get_horoscope(args["sign"])
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps({"horoscope": result}, ensure_ascii=False),
            })

messages.append({"role": "system", "content": "ツールによって生成された運勢のみで応答してください。"})
save_log(messages, "モデルへの追加メッセージ")
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    tools=tools,
    messages=messages,
)

save_log(response.model_dump(), "モデルの最終応答")

# 5. モデルが応答できるはずです！
print("最終出力:")
print(response.choices[0].message.content)