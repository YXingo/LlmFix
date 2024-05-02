import time
import openai


class ChatGPT:

    def __init__(self):
        self.conversation = [
            {"role": "system", "content": "You are a helpful assistant."}]

    def ask_gpt(self, user_input: str) -> str:
        """
        model used is gpt-3.5-turbo
        temperature is set to be 0.0, which is most deterministic and least random
        max_token is default, which is (4096 - prompt tokens)

        Parameter
        ----------
        question : str
            The question to be asked to chatgpt
        """

        self.conversation.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.2,
            max_tokens=1024,
            top_p=0.9,
        )

        answer = response["choices"][0]["message"]["content"]

        self.conversation.append({"role": "assistant", "content": answer})

        return answer

    def safe_ask_gpt(self, user_input: str, max_retries=100, retry_delay=3):
        for attempt in range(max_retries):
            try:
                # 尝试执行 ask_gpt 函数
                response = self.ask_gpt(user_input)
                return response  # 成功则返回响应
            except Exception as e:
                # 捕获异常并检查是否还有重试的机会
                if attempt < max_retries - 1:
                    print(f"连接失败，将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)  # 等待一段时间后重试
                else:
                    print("重试次数用尽，程序中止。")
                    raise e  # 重试用尽后抛出最后一次的异常

    def ask_checker(self, main_gpt_response: str, prompt: str) -> str:
        if main_gpt_response is not None:
            checker_input = main_gpt_response + "\n" + prompt

        else:
            checker_input = prompt

        self.conversation.append({"role": "user", "content": checker_input})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.2,
            max_tokens=1024,
            top_p=0.9,
        )

        answer = response["choices"][0]["message"]["content"]

        self.conversation.append({"role": "assistant", "content": answer})

        return answer

    def manual_add_response(self, response: str):
        self.conversation.append({"role": "assistant", "content": response})

    def clear_context_conversion(self):
        self.conversation = [
            {"role": "system", "content": "You are a helpful assistant."}]

    def __str__(self):
        output = ""
        for conversation in self.conversation:
            output += str(conversation) + "\n"
        output = output.rstrip('\n')
        return output
