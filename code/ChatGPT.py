import time
import openai


class ChatGPT:
    def __init__(self):
        self.conversation = [
            {"role": "system", "content": "You are a helpful assistant."}]

    def ask_gpt(self, user_input: str) -> str:
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
                response = self.ask_gpt(user_input)
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retry in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Stopped.")
                    raise e

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
