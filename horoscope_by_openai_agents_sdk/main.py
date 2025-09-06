# main.py
import asyncio
from agent import HoroscopeAgent

async def async_input(prompt: str) -> str:
    # 入力をスレッドに逃がしてイベントループを止めない
    return await asyncio.to_thread(input, prompt)

async def chat_loop():
    print("=== 占いアシスタントを開始します ===")
    print("（例）こんにちは など自由に話しかけてください。'exit' で終了。")

    agent = HoroscopeAgent()  # セッションを内部で引き継げるなら再利用

    while True:
        try:
            user_input = (await async_input("あなた: ")).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nチャットを終了します。")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("チャットを終了します。")
            break

        try:
            async for line in agent.run(user_input):
                print(f"AI: {line}", end="", flush=True)
            print()  # 最後に改行

        except Exception as e:
            # ここでログ出しや再試行の方針を決める
            print(f"\n[エラー] 応答の取得に失敗しました: {e}")

async def main():
    await chat_loop()

if __name__ == "__main__":
    asyncio.run(main())
