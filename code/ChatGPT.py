import re
import time
import signal
import random
import numpy as np
import openai
import threading
import _thread  # For Python 3.x, use '_thread' instead of 'thread'
from datasets import load_dataset

# Please enter your key
# openai.api_key = "XXX"


# proxy = {
#     'http': 'http://127.0.0.1:22',
#     'https': 'http://127.0.0.1:22'
# }
#
# openai.proxy = proxy


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

    def safe_ask_gpt(self, user_input: str, max_retries=500, retry_delay=3):
        for attempt in range(max_retries):
            try:
                response = self.ask_gpt(user_input)
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"连接失败，将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    print("重试次数用尽，程序中止。")
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


def raise_timeout(signum, frame):
    raise TimeoutError


def execute_with_timeout(func, args=(), kwargs={}, timeout_duration=1):
    def target():
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout_duration)
    if thread.is_alive():
        _thread.interrupt_main()
        thread.join()


def execute_test(candidate_solution, test, entry_point_name):
    global_namespace = {}
    execute_check = """check(""" + entry_point_name + """)"""

    def exec_test():
        exec(candidate_solution, global_namespace)
        exec(test, global_namespace)
        exec(execute_check, global_namespace)

    try:
        exec_test()
        execute_with_timeout(exec_test, timeout_duration=1)
        return True, None
    except Exception as e:
        return False, e


def test_maxnum_samples_X_epochs_openai(chatgpt, dataset, max_num, model, X):
    txt_name = f'output-{model}-{X}epochs.txt'
    file = open('output/' + txt_name, mode='w', encoding='utf-8')

    result = []
    time_result = []

    pre = "Based on the comments in the following Python function, provide the complete implementation of the function. Note: You only need to import the necessary modules or packages, and then give the complete implementation of the function. No other content is required. \n"

    for i in range(X):
        print(f"\n===========\n\n=> epoch{i}:\n")

        all_start_time = time.time()

        num_correct, count = 0, 0
        for sample in dataset['test']:
            single_start_time = time.time()

            task_id = sample['task_id']
            prompt = sample['prompt']
            test = sample['test']
            entry_point = sample['entry_point']

            chatgpt.clear_context_conversion()

            candidate_solution = chatgpt.safe_ask_gpt(pre + prompt)

            print(f"\n--------------------------------------------\n")
            print(
                f"For sample {count}, task_id = {task_id}: \nSolution generated! generated_solution = \n{candidate_solution}")
            file.write('\n--------------------------------------------\n')
            file.write(
                f"For sample {count}, task_id = {task_id}: \nSolution generated! generated_solution = \n{candidate_solution}")

            judge, exception = execute_test(candidate_solution, test, entry_point)

            single_end_time = time.time()

            if judge:
                num_correct += 1
                print(f"\nepoch {i} sample {count}: \n\nTest result: Pass the test.")
                file.write(f"\nepoch {i} sample {count}: \n\nTest result: Pass the test.")
            else:
                print(
                    f"\nepoch {i} sample {count}: \n\nTest result: Fail the test.\nException type: {type(exception).__name__}\nException message: {str(exception)}")
                file.write(
                    f"\nepoch {i} sample {count}: \n\nTest result: Fail the test.\nException type: {type(exception).__name__}\nException message: {str(exception)}")

            print(f"\nTime taken: {single_end_time - single_start_time} seconds.")
            file.write(f"\nTime taken: {single_end_time - single_start_time} seconds.")

            count += 1

            print('\n--------------------------------------------\n')
            file.write('\n--------------------------------------------\n')
            file.flush()

            if (count >= max_num):
                break

        all_end_time = time.time()
        accuracy = num_correct / max_num
        result.append(accuracy)
        time_result.append(all_end_time - all_start_time)
        print(f"epoch {i} Model accuracy: {accuracy * 100:.2f}%\nTime taken: {all_end_time - all_start_time} seconds.")
        file.write(
            f"epoch {i} Model accuracy: {accuracy * 100:.2f}%\nTime taken: {all_end_time - all_start_time} seconds.")
        file.flush()

    print(f"\n~~~~~~~~~~~~~\n\nSummary: \n")
    for index, a in enumerate(result):
        print(f"epoch {index} accuracy: {a * 100:.2f}%")
        file.write(f"\nepoch {index} accuracy: {a * 100:.2f}%")

    for index, a in enumerate(time_result):
        print(f"epoch {index} time taken: {a} seconds")
        file.write(f"\nepoch {index} time taken: {a} seconds")

    print(f"average accuracy: {sum(result) / len(result)}")
    print(f"average time taken: {sum(time_result) / len(time_result)}")
    file.write(f"average accuracy: {sum(result) / len(result)}")
    file.write(f"average time taken: {sum(time_result) / len(time_result)}")

    file.close()


if __name__ == '__main__':
    gpt = ChatGPT()
    dataset = load_dataset("openai_humaneval")
    test_maxnum_samples_X_epochs_openai(gpt, dataset, max_num=164, model='gpt-3.5-turbo', X=10)
