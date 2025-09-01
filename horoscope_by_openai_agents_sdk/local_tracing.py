from __future__ import annotations
import json
import os
import datetime
from typing import Any, Dict, List, DefaultDict
from collections import defaultdict
from agents.tracing.processor_interface import TracingProcessor  # Agents SDK 抽象

LOG_DIR = "logs"
JSONL_PATH = os.path.join(LOG_DIR, "agents_traces.jsonl")
os.makedirs(LOG_DIR, exist_ok=True)

def _now_ms() -> int:
    """ms epoch（SDKのeventに似せたタイムスタンプ）"""
    import time
    return int(time.time() * 1000)

def _write_jsonl(kind: str, payload: Dict[str, Any]) -> None:
    """JSONLに1行追記"""
    rec = {"ts": _now_ms(), "kind": kind, **payload}
    with open(JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def _md_escape(s: str) -> str:
    """Markdown向けの軽いエスケープ"""
    return s.replace("<", "&lt;").replace(">", "&gt;")

def _to_pretty_json(val: Any) -> str:
    """オブジェクト/文字列いずれも、可能ならJSON整形して返す。無理ならそのまま文字列化。"""
    try:
        if isinstance(val, str):
            # JSON文字列ならパースして整形
            return json.dumps(json.loads(val), ensure_ascii=False, indent=2)
        else:
            # すでに dict/list ならそのまま整形
            return json.dumps(val, ensure_ascii=False, indent=2)
    except Exception:
        return str(val)

class LocalJsonlAndPrettyProcessor(TracingProcessor):
    """
    Agents SDK のトレースをローカルに保存:
      - JSONL: すべての trace/span イベントを 1行/レコードで追記（要約）
      - Markdown: 1回の Runner.run()（=1 trace）ごとに、全文のタイムラインを1ファイルに出力（シンプル）
        例) logs/run-trace-YYYYMMDD-HHMMSS-<trace_id>.md
    OpenAI への送信は行わない（set_trace_processors([このクラス()]) で既定置換）
    """

    def __init__(self):
        # trace_id -> Markdownの行バッファ
        self._md_lines: DefaultDict[str, List[str]] = defaultdict(list)

    # ---------------- Trace lifecycle ----------------

    def on_trace_start(self, trace) -> None:
        tid = trace.trace_id
        workflow = getattr(trace, "workflow_name", None) or "Agent Run"
        metadata = getattr(trace, "metadata", None)

        # JSONL
        _write_jsonl("trace_start", {
            "trace_id": tid,
            "workflow_name": workflow,
            "group_id": getattr(trace, "group_id", None),
            "metadata": metadata,
        })

        # Markdown（シンプルヘッダ）
        lines = self._md_lines[tid]
        lines.append(f"# Run Trace {tid}")
        lines.append(f"- **Workflow:** `{_md_escape(workflow)}`")
        if metadata:
            lines.append("- **Metadata:**")
            lines.append("```json")
            lines.append(_to_pretty_json(metadata))
            lines.append("```")
        lines.append("---")
        lines.append("## Spans")

    def on_trace_end(self, trace) -> None:
        tid = trace.trace_id
        workflow = getattr(trace, "workflow_name", None) or "Agent Run"
        duration = getattr(trace, "duration_ms", None)
        ok = getattr(trace, "ok", None)
        err = getattr(trace, "error", None)

        # JSONL
        _write_jsonl("trace_end", {
            "trace_id": tid,
            "workflow_name": workflow,
            "metadata": getattr(trace, "metadata", None),
            "duration_ms": duration,
            "ok": ok,
            "error": err,
        })

        # Markdown フッタ（シンプル）
        lines = self._md_lines.get(tid, [])
        lines.append("")
        lines.append("---")
        lines.append("## Summary")
        lines.append(f"- **Duration:** {duration} ms")
        lines.append(f"- **Result:** {'OK' if ok else 'ERROR'}")
        if err:
            lines.append(f"- **Error:** `{_md_escape(str(err))}`")

        # 1 RUN = 1 ファイル（日時入りファイル名）
        now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        md_path = os.path.join(LOG_DIR, f"run-trace-{now_str}-{tid}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        # 後始末
        self._md_lines.pop(tid, None)

    # ---------------- Span lifecycle ----------------

    def on_span_start(self, span) -> None:
        tid = span.trace_id
        name = getattr(span, "name", "")
        typ = getattr(getattr(span, "span_data", None), "type", None)

        # JSONL
        _write_jsonl("span_start", {
            "trace_id": tid,
            "span_id": span.span_id,
            "parent_id": getattr(span, "parent_id", None),
            "name": name,
            "type": typ,
        })

        # Markdown：見出しだけ（詳細は end で書く）
        self._md_lines[tid].append(f"### {name}  _(type: {typ})_")

    def on_span_end(self, span) -> None:
        tid = span.trace_id
        name = getattr(span, "name", "")
        duration = getattr(span, "duration_ms", None)
        ok = getattr(span, "ok", None)
        err = getattr(span, "error", None)
        data = getattr(span, "span_data", None)

        # JSONL（要約）
        _write_jsonl("span_end", {
            "trace_id": tid,
            "span_id": span.span_id,
            "parent_id": getattr(span, "parent_id", None),
            "name": name,
            "duration_ms": duration,
            "ok": ok,
            "error": err,
            "data": self._summarize_span_data(data),
        })

        # Markdown（シンプル & 全文）
        lines = self._md_lines[tid]
        lines.append(f"- **Duration:** {duration} ms")
        lines.append(f"- **Result:** {'OK' if ok else 'ERROR'}")
        if err:
            lines.append(f"- **Error:** `{_md_escape(str(err))}`")

        if data:
            t = getattr(data, "type", None)
            if t == "generation":
                model = getattr(data, "model", None)
                inp = getattr(data, "input", None)
                out = getattr(data, "output", None)
                usage = getattr(data, "usage", None)

                if model:
                    lines.append(f"- **Model:** `{_md_escape(str(model))}`")

                # 入力（全文）
                if inp is not None:
                    lines.append("- **Input:**")
                    # JSONとして整形できればjson、無理ならそのまま
                    pretty_in = _to_pretty_json(inp)
                    # JSONだった場合は ```json、そうでなければ ```（見た目の判断は簡略化）
                    is_jsonish = pretty_in.startswith("{") or pretty_in.startswith("[")
                    fence = "```json" if is_jsonish else "```"
                    lines.append(fence)
                    lines.extend(pretty_in.splitlines())
                    lines.append("```")

                # 出力（全文）
                if out is not None:
                    lines.append("- **Output:**")
                    pretty_out = _to_pretty_json(out)
                    is_jsonish = pretty_out.startswith("{") or pretty_out.startswith("[")
                    fence = "```json" if is_jsonish else "```"
                    lines.append(fence)
                    lines.extend(pretty_out.splitlines())
                    lines.append("```")

                # 使用量
                if usage:
                    lines.append("- **Usage:**")
                    lines.append("```json")
                    lines.extend(json.dumps(usage, ensure_ascii=False, indent=2).splitlines())
                    lines.append("```")

            elif t == "function":
                tool = getattr(data, "name", None)
                args = getattr(data, "input", None)
                out = getattr(data, "output", None)

                if tool:
                    lines.append(f"- **Tool:** `{_md_escape(str(tool))}`")

                if args is not None:
                    lines.append("- **Args:**")
                    pretty_args = _to_pretty_json(args)
                    is_jsonish = pretty_args.startswith("{") or pretty_args.startswith("[")
                    fence = "```json" if is_jsonish else "```"
                    lines.append(fence)
                    lines.extend(pretty_args.splitlines())
                    lines.append("```")

                if out is not None:
                    lines.append("- **Result:**")
                    pretty_out = _to_pretty_json(out)
                    is_jsonish = pretty_out.startswith("{") or pretty_out.startswith("[")
                    fence = "```json" if is_jsonish else "```"
                    lines.append(fence)
                    lines.extend(pretty_out.splitlines())
                    lines.append("```")

        # 区切り
        lines.append("")

    # ---------------- lifecycle（抽象メソッドの実装） ----------------

    def shutdown(self, *args, **kwargs) -> None:
        """必要ならここで明示的 flush/close を実装（今回はNOP）"""
        pass

    def force_flush(self, *args, **kwargs) -> None:
        """必要ならここでバッファ強制フラッシュ（今回はNOP）"""
        pass

    # ---------------- helpers（JSONL側は要約でOK） ----------------

    def _summarize_span_data(self, data) -> Dict[str, Any]:
        """JSONL側に載せる軽量サマリ（サイズ爆発防止）"""
        if not data:
            return {}
        t = getattr(data, "type", None)
        if t == "generation":
            return {
                "type": t,
                "model": getattr(data, "model", None),
                # JSONLはプレビューでOK（全文はMDに出す）
                "input_preview": _safe_preview(getattr(data, "input", None)),
                "output_preview": _safe_preview(getattr(data, "output", None)),
                "usage": getattr(data, "usage", None),
            }
        if t == "function":
            return {
                "type": t,
                "name": getattr(data, "name", None),
                "args_preview": _safe_preview(getattr(data, "input", None)),
                "result_preview": _safe_preview(getattr(data, "output", None)),
            }
        return {"type": t}

def _safe_preview(val: Any, n: int = 500) -> str:
    """JSONL用の軽いプレビュー（安全のため切り詰め）"""
    if val is None:
        return ""
    s = str(val)
    return s if len(s) <= n else s[:n] + "…"
