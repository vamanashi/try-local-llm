import json
import functools

LOG = "\033[36m"  # シアン色
TOOL_LOG = "\033[33m"  # 黄色
CALL_LLM_LOG = "\033[35m"  # 紫色
RESET = "\033[0m"  # 色リセット

def log_action(func):
    """メソッドの実行をログ出力"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # ツール系メソッド名で色分岐
        if func.__name__ == "_call_llm":
            color = CALL_LLM_LOG
        elif func.__name__.startswith("_call_tool"):
            color = TOOL_LOG
        else:
            color = LOG
        print(f"{color}[LOG] → {func.__name__} 開始{RESET}")
        # _call_llmの場合はプロンプトをログ出力
        if func.__name__ == "_call_llm" and args:
            messages = args[0]
            # tool_callsがあればdict化
            def safe_dict(obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump()
                elif isinstance(obj, list):
                    return [safe_dict(x) for x in obj]
                elif isinstance(obj, dict):
                    return {k: safe_dict(v) for k, v in obj.items()}
                else:
                    return obj
            messages_safe = safe_dict(messages)
            print(f"{color}[LOG] プロンプト: {json.dumps(messages_safe, ensure_ascii=False, indent=2)}{RESET}")
        result = func(self, *args, **kwargs)
        # ログ出力時のみdict化して見やすく表示
        if hasattr(result, "model_dump"):
            print(f"{color}[LOG] {json.dumps(result.model_dump(), ensure_ascii=False, indent=2)}{RESET}")
        else:
            print(f"{color}[LOG] {result}{RESET}")
        print(f"{color}[LOG] ← {func.__name__} 完了{RESET}")
        return result
    return wrapper