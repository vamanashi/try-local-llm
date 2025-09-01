# ===========================
# tools
# ===========================

# モデル用の呼び出し可能なツールのリストを定義
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_lucky_item",
            "description": "星座や運勢から今日のラッキーアイテムを取得します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sign": {
                        "type": "string",
                        "description": "牡牛座や水瓶座などの占星術のサイン",
                    },
                    "fortune": {
                        "type": "string",
                        "description": "星座に関連する運勢の内容",
                    }
                },
                "required": ["sign", "fortune"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_zodiac_sign",
            "description": "誕生日から星座を判定します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "birthday": {
                        "type": "string",
                        "description": "YYYY-MM-DD形式の誕生日",
                    }
                },
                "required": ["birthday"],
            },
        },
    },
]

def get_horoscope(sign):
    """星座から今日の運勢を取得するツール"""
    # ダミー実装
    return f"{sign}: 来週の火曜日にあなたは赤ちゃんのカワウソと友達になるでしょう。"

def get_lucky_item(sign):
    """
    ラッキーアイテム提案ツール
    星座や運勢から今日持つと良いアイテムを返す。
    """
    # ダミー実装
    return f"{sign}の今日のラッキーアイテムは「水色のハンカチ」です。"

def get_zodiac_sign(birthday):
    """
    誕生日から星座判定ツール
    誕生日（YYYY-MM-DD）を入力すると星座名を返す。
    """
    # ダミー実装
    return "山羊座"
