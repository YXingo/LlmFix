import re
import time
import signal
import ChatGPT
import modules_db
import statistics


def raise_timeout(signum, frame):
    raise TimeoutError


def get_last_function(code):
    return re.sub(r'def .+?\n(?=def |\Z)', '', code, flags=re.DOTALL)


def get_and_remove_last_function(code):
    split_lines = re.split(r'(?m)^(def)', code)
    last_function = ''.join(split_lines[-2:])
    new_code = ''.join(split_lines[:-2])
    return [last_function, new_code]


def filter(code: str) -> str:
    if '```python' in code:
        def_line = code.index('```python')
        code = code[def_line:].strip()
        code = code.replace('```python', '')
        try:
            next_line = code.index('```')
            code = code[:next_line].strip()
        except:
            pass

        code.replace("    ", "\t").replace("   ", "\t").replace("  ", "\t").replace("\t", "    ")

    code = code.split('if __name__ == "__main__":')[0]
    code = code.split("if __name__ == '__main__':")[0]

    lines = code.split('\n')
    new_lines = []
    for line in lines:
        if not (line.strip().startswith('print') or line.strip().startswith('input') or line.strip().startswith(
                'assert') or line.strip().startswith('unittest')):
            new_lines.append(line)
    code = '\n'.join(new_lines)

    return code


def execute_test(candidate_solution, test, entry_point_name=None, mbpp=False):
    global_namespace = {}

    if mbpp:
        test_multi_lines = '\n'.join(test)

        try:
            signal.signal(signal.SIGALRM, raise_timeout)
            signal.alarm(1)

            exec(candidate_solution, global_namespace)
            exec(test_multi_lines, global_namespace)

            signal.alarm(0)

            return True, None
        except Exception as e:

            signal.alarm(0)
            return False, e
    else:
        execute_check = """check(""" + entry_point_name + """)"""

        try:
            signal.signal(signal.SIGALRM, raise_timeout)
            signal.alarm(1)

            exec(candidate_solution, global_namespace)
            exec(test, global_namespace)
            exec(execute_check, global_namespace)

            signal.alarm(0)

            return True, None
        except Exception as e:

            signal.alarm(0)
            return False, e


def add_import_statement(missing_name, code):
    module_name, fc_name, import_statement = None, None, ""

    if missing_name in modules_db.modules:
        import_statement = f"import {missing_name}\n\n"
    elif missing_name in modules_db.fcs:
        import_statement = f"from {modules_db.fcs[missing_name]} import {missing_name}\n\n"

    if missing_name == 'np':
        import_statement = "import numpy as np\n\n"

    code = import_statement + code
    return code


def get_missing_name(exception_message):
    match = re.search(r"name '(.+?)' is not defined", exception_message)
    if match:
        return match.group(1)
    else:
        return None


def print_test_result(judge, exception=None, log_file=None, final=False):
    if final:
        ex = 'Final '
    else:
        ex = ''

    if judge:
        print(f"{ex}Test result: Pass the test.\n", file=log_file)
        print(f"{ex}Test result: Pass the test.\n")
    else:
        print(f"{ex}Test result: Fail the test.\n"
              f"Exception type: {type(exception).__name__}\n"
              f"Exception message: {str(exception)}\n", file=log_file)
        print(f"{ex}Test result: Fail the test.\n"
              f"Exception type: {type(exception).__name__}\n"
              f"Exception message: {str(exception)}\n")


def test_single_sample(code, dataset, id, log_file=None, mbpp=False):
    code = filter(code)
    print(f"\n- - - - - - - - - - - - - - -\nfilter result: "
          f"\n\n{code}\n- - - - - - - - - - - - - - -\n", file=log_file)
    print(f"\n- - - - - - - - - - - - - - -\nfilter result: "
          f"\n\n{code}\n- - - - - - - - - - - - - - -\n")

    judge = False
    while not judge:
        try:
            compile(source=code, filename='', mode='exec')
            judge = True
        except Exception as e:
            print_test_result(judge, e, log_file)
            code = get_and_remove_last_function(code)[1]
            judge = False
            print(f"\n- - - - - - - - - - - - - - -\nFix compilation stage exceptions result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n", file=log_file)
            print(f"\n- - - - - - - - - - - - - - -\nFix compilation stage exceptions result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n")

    if mbpp:
        sample = dataset['test'][id]
        test = sample['test_list']

        judge, exception = execute_test(code, test, mbpp=mbpp)
    else:
        sample = dataset['test'][id]
        test = sample['test']
        entry_point = sample['entry_point']

        judge, exception = execute_test(code, test, entry_point, mbpp=mbpp)

    print_test_result(judge, exception, log_file)

    if not judge:
        if type(exception).__name__ == 'NameError':
            while True:
                fixed_code = add_import_statement(get_missing_name(str(exception)), code)

                if code == fixed_code or judge:
                    break
                else:
                    code = fixed_code

                if mbpp:
                    judge, exception = execute_test(code, test, mbpp=mbpp)
                else:
                    judge, exception = execute_test(code, test, entry_point, mbpp=mbpp)

            if mbpp:
                judge, exception = execute_test(code, test, mbpp=mbpp)
            else:
                judge, exception = execute_test(code, test, entry_point, mbpp=mbpp)
            print(f"\n- - - - - - - - - - - - - - -\nfix NameError result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n", file=log_file)
            print(f"\n- - - - - - - - - - - - - - -\nfix NameError result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n")
            print_test_result(judge, exception, log_file)

    return code, judge, exception


def test_all_samples(pipe, dataset, log_file=None, mbpp=False, epoch=None, test_dataset=None, GPT=False):
    if not pipe:
        gpt = ChatGPT.ChatGPT()
        pre = "Based on the comments in the following Python function, provide the complete implementation of the function. Note: You only need to give the complete implementation of the function. No other content is required. \n"

    all_start_time = time.time()
    num_correct, count = 0, 0

    for sample in dataset['test']:
        task_id = sample['task_id']
        prompt = sample['prompt']

        # WizardCoder uses below
        # prompt = f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\nComplete the following Python code without any tests or explanation\n{prompt}\n\n### Response:\n```python"""

        single_start_time = time.time()

        if pipe:
            code = pipe(prompt, max_length=1024, do_sample=True, temperature=0.2, top_p=0.9)[0]['generated_text']
        else:
            gpt.clear_context_conversion()
            code = gpt.safe_ask_gpt(pre + prompt)

        single_end_time = time.time()

        print(f"\n--------------------------------------------\n\n"
              f"For sample {count}, task_id = {task_id}, "
              f"generation time is {single_end_time - single_start_time}s.\n"
              f"Original generated result: "
              f"\n\n{code}\n\n- - - - - - - - - - - - - - -\n\n", file=log_file)
        print(f"\n--------------------------------------------\n\n"
              f"For sample {count}, task_id = {task_id}, "
              f"generation time is {single_end_time - single_start_time}s.\n"
              f"Original generated result: "
              f"\n\n{code}\n\n- - - - - - - - - - - - - - -\n\n")

        if mbpp:
            code, judge, exception = test_single_sample(code, test_dataset, count, log_file, mbpp=mbpp)
        else:
            code, judge, exception = test_single_sample(code, dataset, count, log_file, mbpp=mbpp)

        print(f"\n- - - - - - - - - - - - - - -\n\n"
              f"Final result: \n\n{code}\n\n", file=log_file)
        print(f"\n- - - - - - - - - - - - - - -\n\n"
              f"Final result: \n\n{code}\n\n")

        print(f"\nFor epoch {epoch}, sample {count}: \n\n")
        print_test_result(judge, exception, log_file, final=True)

        if judge:
            num_correct += 1
        count += 1

        print('\n--------------------------------------------\n', file=log_file)
        print('\n--------------------------------------------\n')
        log_file.flush()

    all_end_time = time.time()
    accuracy = num_correct / len(dataset['test'])
    print(f"For epoch {epoch}, accuracy: {accuracy * 100:.2f}%\n"
          f"Time taken: {all_end_time - all_start_time}s.", file=log_file)
    print(f"For epoch {epoch}, accuracy: {accuracy * 100:.2f}%\n"
          f"Time taken: {all_end_time - all_start_time}s.")
    log_file.flush()

    return accuracy, all_end_time - all_start_time


def test_multiple_times(pipe, dataset, log_file=None, mbpp=False, times=10, test_dataset=None, GPT=False):
    all_accuracies, all_times = [], []

    for i in range(times):
        print(f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n=> Epoch {i}: ", file=log_file)
        print(f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n=> Epoch {i}: ")

        accuracy, time = test_all_samples(pipe, dataset, log_file, mbpp=mbpp, epoch=i,
                                          test_dataset=test_dataset, GPT=GPT)

        all_accuracies.append(accuracy)
        all_times.append(time)

    print(f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\nSummary: \n\n", file=log_file)
    print(f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\nSummary: \n\n")

    for index, a in enumerate(all_times):
        print(f"epoch {index} time taken: {a} seconds", file=log_file)
        print(f"epoch {index} time taken: {a} seconds")
    print(f"average time taken: {statistics.mean(all_times)}\n\n", file=log_file)
    print(f"average time taken: {statistics.mean(all_times)}\n\n")

    for index, a in enumerate(all_accuracies):
        print(f"epoch {index} accuracy: {a * 100:.2f}%\n", file=log_file)
        print(f"epoch {index} accuracy: {a * 100:.2f}%\n")
    print(f"average accuracy: {statistics.mean(all_accuracies)}\n"
          f"min accuracy: {min(all_accuracies)}\n"
          f"max accuracy: {max(all_accuracies)}\n"
          f"Std Dev: {statistics.stdev(all_accuracies)}\n", file=log_file)
    print(f"average accuracy: {statistics.mean(all_accuracies)}\n"
          f"min accuracy: {min(all_accuracies)}\n"
          f"max accuracy: {max(all_accuracies)}\n"
          f"Std Dev: {statistics.stdev(all_accuracies)}\n")
