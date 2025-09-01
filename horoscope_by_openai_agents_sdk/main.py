# ===========================
# main
# ===========================
from agent import HoroscopeAgent
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
import asyncio

if __name__ == "__main__":

    print("=== 占いアシスタントを開始します ===")
    print("（例）こんにちは など自由に話しかけてください。'exit' で終了。")

    horoscope_agent = HoroscopeAgent()

    # チャット開始
    # exitしない限り、チャットを続ける
    while True:
        user_input = input("あなた: ")

        if user_input.lower() in ["exit", "quit"]:
            print("チャットを終了します。")
            break

        result = asyncio.run(horoscope_agent.run(user_input))
        
        print("AI: ", result)