from __future__ import annotations

import os
import json
from typing import List, Optional, Any

from agents.memory.session import SessionABC
from agents.items import TResponseInputItem


class JSONLSession(SessionABC):
    """
    シンプルな JSONL バックエンドのカスタムセッション。

    - `logs/sessions/{session_id}.jsonl` に会話アイテムを逐次保存
    - 同一プロセス内ではメモリキャッシュを使用して高速化
    - アイテムは JSON シリアライズ可能な辞書として保持
    """

    def __init__(self, session_id: str, base_dir: Optional[str] = None):
        self.session_id = session_id
        module_dir = os.path.dirname(__file__)
        self.base_dir = base_dir or os.path.join(module_dir, "logs", "sessions")
        self.path = os.path.join(self.base_dir, f"{session_id}.jsonl")
        self._items: List[TResponseInputItem] = []
        self._loaded = False

    # -----------------------------
    #  内部ユーティリティ
    # -----------------------------
    def _ensure_dir(self) -> None:
        os.makedirs(self.base_dir, exist_ok=True)

    def _to_jsonable(self, item: Any) -> Any:
        """可能な限り JSON に変換。失敗時は文字列化。"""
        if item is None:
            return None
        if isinstance(item, (str, int, float, bool)):
            return item
        if isinstance(item, (list, tuple)):
            return [self._to_jsonable(x) for x in item]
        if isinstance(item, dict):
            return {k: self._to_jsonable(v) for k, v in item.items()}
        for attr in ("model_dump", "dict"):
            fn = getattr(item, attr, None)
            if callable(fn):
                try:
                    data = fn()
                    return self._to_jsonable(data)
                except Exception:
                    pass
        return str(item)

    def _load_if_needed(self) -> None:
        if self._loaded:
            return
        self._items = []
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        self._items.append(obj)
            except Exception:
                self._items = []
        self._loaded = True

    def _rewrite_file(self) -> None:
        """全アイテムを書き戻し。pop/clear 用。"""
        self._ensure_dir()
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                for it in self._items:
                    f.write(json.dumps(self._to_jsonable(it), ensure_ascii=False))
                    f.write("\n")
        except Exception:
            pass

    # -----------------------------
    #  SessionABC 実装
    # -----------------------------
    async def get_items(self, limit: int | None = None) -> List[TResponseInputItem]:
        self._load_if_needed()
        if limit is None or limit >= len(self._items):
            return list(self._items)
        return list(self._items[-limit:])

    async def add_items(self, items: List[TResponseInputItem]) -> None:
        if not items:
            return
        self._load_if_needed()
        self._items.extend(items)
        # 逐次でファイルに追記
        self._ensure_dir()
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                for it in items:
                    f.write(json.dumps(self._to_jsonable(it), ensure_ascii=False))
                    f.write("\n")
        except Exception:
            pass

    async def pop_item(self) -> TResponseInputItem | None:
        self._load_if_needed()
        if not self._items:
            return None
        last = self._items.pop()
        self._rewrite_file()
        return last

    async def clear_session(self) -> None:
        self._load_if_needed()
        self._items.clear()
        # ファイルを空にする（存在すれば）
        try:
            if os.path.exists(self.path):
                with open(self.path, "w", encoding="utf-8") as f:
                    f.truncate(0)
        except Exception:
            pass

