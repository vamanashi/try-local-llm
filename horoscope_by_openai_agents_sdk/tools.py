# ===========================
# tools
# ===========================
from agents import function_tool

@function_tool
def get_horoscope(sign: str) -> str:
    """
    星座名から今日の運勢を取得するツール。

    Args:
        sign (str): 占星術のサイン（例: "牡牛座", "水瓶座" など）
    Returns:
        str: 今日の運勢メッセージ。
    """
    # ダミー実装
    return f"{sign}: 来週の火曜日にあなたは赤ちゃんのカワウソと友達になるでしょう。"

@function_tool
def get_lucky_item(sign: str) -> str:
    """
    星座名から今日のラッキーアイテムを提案するツール。

    Args:
        sign (str): 占星術のサイン（例: "牡牛座", "水瓶座" など）
    Returns:
        str: 今日持つと良いラッキーアイテム。
    """
    # ダミー実装
    return f"{sign}の今日のラッキーアイテムは「水色のハンカチ」です。"

@function_tool
def get_zodiac_sign(birthday: str) -> str:
    """
    誕生日から星座名を判定するツール。

    Args:
        birthday (str): YYYY-MM-DD形式の誕生日（例: "1990-01-25"）
    Returns:
        str: 判定された星座名、またはエラーメッセージ。
    """
    # ダミー実装
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", birthday):
        return "不正な日付形式です。YYYY-MM-DD形式で入力してください。"
    else:
        return "水瓶座"
