from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from agents import ItemHelpers
import json
import os


class AgentLogEntry(BaseModel):
    """エージェントの出力を表す統一ログエントリ。

    SDK のイベント/アイテム種別に依存せず、シンプルで一貫した形で保持します。
    """

    type: str  # 例: "agent_updated", "tool_call", "tool_output", "message_output"
    text: str  # 事前整形済みの文字列（必要に応じて改行を含む）
    raw_event_type: Optional[str] = None  # デバッグ用の元 SDK イベント/アイテム種別
    data: Optional[Dict[str, Any]] = None  # 任意の構造化ペイロード
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def format(self) -> str:
        """ストリーミング/表示用の文字列を返します。"""
        return self.text


class AgentHistory(BaseModel):
    """エージェント出力のメモリ内履歴を管理するクラス。

    インターフェースは最小限で、`handle_event` ひとつで SDK イベントを
    統一ログエントリに変換し、ストリーム出力用の文字列を返します
    （無視すべきイベントは None を返します）。
    """

    entries: List[AgentLogEntry] = Field(default_factory=list)

    # -----------------------------
    #  ユーザー入力の記録
    # -----------------------------
    def add_user_input(self, text: str) -> AgentLogEntry:
        """ユーザーからの入力テキストを履歴に追加します。"""
        entry = AgentLogEntry(
            type="user_input",
            text=f"User: {text}\n",
            raw_event_type="user_input",
            data={"content": text},
        )
        self.entries.append(entry)
        return entry

    def handle_event(self, event: Any) -> Optional[str]:
        """SDK イベントを統一ログエントリへ変換し、履歴に追加します。

        ストリーム出力用に整形された文字列を返します（出力不要の場合は None）。
        """

        # 低レベルな差分イベントは無視
        if getattr(event, "type", None) == "raw_response_event":
            return None

        # エージェント更新イベント
        if getattr(event, "type", None) == "agent_updated_stream_event":
            name = getattr(getattr(event, "new_agent", None), "name", None)
            text = f"Agent updated: {name}\n"
            entry = AgentLogEntry(
                type="agent_updated",
                text=text,
                raw_event_type="agent_updated_stream_event",
                data={"agent_name": name} if name else None,
            )
            self.entries.append(entry)
            return entry.format()

        # 生成アイテム（ツール/メッセージ出力）
        if getattr(event, "type", None) == "run_item_stream_event":
            item = getattr(event, "item", None)
            item_type = getattr(item, "type", None)

            if item_type == "tool_call_item":
                tool_name = getattr(item, "tool_name", None)
                text = "-- Tool was called\n"
                entry = AgentLogEntry(
                    type="tool_call",
                    text=text,
                    raw_event_type=item_type,
                    data={"tool": tool_name} if tool_name else None,
                )
                self.entries.append(entry)
                return entry.format()

            if item_type == "tool_call_output_item":
                output = getattr(item, "output", None)
                text = f"-- Tool output: {output}\n"
                entry = AgentLogEntry(
                    type="tool_output",
                    text=text,
                    raw_event_type=item_type,
                    data={"output": output} if output is not None else None,
                )
                self.entries.append(entry)
                return entry.format()

            if item_type == "message_output_item":
                try:
                    msg = ItemHelpers.text_message_output(item)
                except Exception:
                    msg = None
                text = f"-- Message output:\n {msg}\n"
                entry = AgentLogEntry(
                    type="message_output",
                    text=text,
                    raw_event_type=item_type,
                    data={"message": msg} if msg is not None else None,
                )
                self.entries.append(entry)
                return entry.format()

            # 既知でない item.type は無視（従来の挙動を維持）
            return None

        # その他のイベント種別も無視（従来の挙動を維持）
        return None

    # -----------------------------
    #  永続化（任意で呼び出し）
    # -----------------------------
    def _ensure_dir(self, path: str) -> None:
        """ファイルの親ディレクトリを作成します（存在しない場合）。"""
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def persist_entry(
        self,
        entry: AgentLogEntry,
        jsonl_path: Optional[str] = None,
    ) -> None:
        """単一エントリを JSONL に追記保存します。"""
        if not jsonl_path:
            return
        self._ensure_dir(jsonl_path)
        try:
            with open(jsonl_path, "a", encoding="utf-8") as f:
                payload = entry.model_dump(mode="json")
                f.write(json.dumps(payload, ensure_ascii=False))
                f.write("\n")
        except Exception:
            # 保存失敗は動作に影響させない（静かに無視）
            pass

    def persist_last(
        self,
        jsonl_path: Optional[str] = None,
    ) -> None:
        """最後のエントリを JSONL に追記保存します。"""
        if not self.entries:
            return
        self.persist_entry(self.entries[-1], jsonl_path=jsonl_path)
