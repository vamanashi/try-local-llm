# ===========================
# main
# ===========================

if __name__ == "__main__":
    from agent import *

    horoscope_agent = HoroscopeAgent()

    # チャット開始
    # exitしない限り、チャットを続ける
    while True:
        user_input = input("あなた: ")

        if user_input.lower() in ["exit", "quit"]:
            print("チャットを終了します。")
            break

        meg = horoscope_agent.run(user_input=user_input)
        print("AI: ", meg)