import re
import time
import signal
import modules_db
import statistics
from datasets import load_dataset


def raise_timeout(signum, frame):
    raise TimeoutError


def get_last_function(code):
    return re.sub(r'def .+?\n(?=def |\Z)', '', code, flags=re.DOTALL)


def remove_last_function(code):
    return code[:code.rfind(get_last_function(code))].rstrip()


def get_and_remove_last_function(code):
    split_lines = re.split(r'(?m)^(def)', code)
    last_function = ''.join(split_lines[-2:])
    new_code = ''.join(split_lines[:-2])
    return [last_function, new_code]


def remove_last_row(code):
    lines = code.split('\n')
    new_lines = lines[:-1]
    code = '\n'.join(new_lines)
    return code


def filter(code: str) -> str:
    code.replace("    ", "\t").replace("   ", "\t").replace("  ", "\t").replace("\t", "    ")
    code = code.split('if __name__ == "__main__":')[0]
    code = code.split("if __name__ == '__main__':")[0]
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        if not (line.strip().startswith('print') or line.strip().startswith('input') or line.strip().startswith(
                'assert')):
            new_lines.append(line)
    code = '\n'.join(new_lines)

    return code


def execute_test(candidate_solution, test, entry_point_name):
    global_namespace = {}
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


def test_single_sample(code, dataset, id, log_file=None):
    sample = dataset['test'][id]

    test = sample['test']
    entry_point = sample['entry_point']

    code = filter(code)
    print(f"\n- - - - - - - - - - - - - - -\nfilter result: "
          f"\n\n{code}\n- - - - - - - - - - - - - - -\n", file=log_file)
    print(f"\n- - - - - - - - - - - - - - -\nfilter result: "
          f"\n\n{code}\n- - - - - - - - - - - - - - -\n")

    judge, exception = execute_test(code, test, entry_point)
    print_test_result(judge, exception, log_file)

    if not judge:
        while type(exception).__name__ == 'SyntaxError' or code == '':
            code = get_and_remove_last_function(code)[1]
            judge, exception = execute_test(code, test, entry_point)
            print(f"\n- - - - - - - - - - - - - - -\nfix SyntaxError result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n", file=log_file)
            print(f"\n- - - - - - - - - - - - - - -\nfix SyntaxError result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n")
            print_test_result(judge, exception, log_file)

        if type(exception).__name__ == 'NameError':
            while True:
                fixed_code = add_import_statement(get_missing_name(str(exception)), code)
                if code == fixed_code or judge:
                    break
                else:
                    code = fixed_code

                judge, exception = execute_test(code, test, entry_point)

            judge, exception = execute_test(code, test, entry_point)
            print(f"\n- - - - - - - - - - - - - - -\nfix NameError result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n", file=log_file)
            print(f"\n- - - - - - - - - - - - - - -\nfix NameError result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n")
            print_test_result(judge, exception, log_file)

        if not judge:
            while True:
                if code == '' or get_and_remove_last_function(code)[1] == '' or judge:
                    break
                code = get_and_remove_last_function(code)[1]
                judge, exception = execute_test(code, test, entry_point)
            print(f"\n- - - - - - - - - - - - - - -\nremove needless functions result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n", file=log_file)
            print(f"\n- - - - - - - - - - - - - - -\nremove needless functions result: "
                  f"\n\n{code}\n- - - - - - - - - - - - - - -\n")

    return code, judge, exception


def test_all_samples(pipe, dataset, log_file=None, epoch=None):
    all_start_time = time.time()
    num_correct, count = 0, 0

    for sample in dataset['test']:
        task_id = sample['task_id']
        prompt = sample['prompt']

        single_start_time = time.time()
        code = pipe(prompt, max_length=1024, do_sample=True, temperature=0.2, top_p=0.9)[0]['generated_text']
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

        code, judge, exception = test_single_sample(code, dataset, count, log_file)

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


def test_multiple_times(pipe, dataset, log_file=None, times=10):
    all_accuracies, all_times = [], []

    for i in range(times):
        print(f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n=> Epoch {i}: ", file=log_file)
        print(f"\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n=> Epoch {i}: ")

        accuracy, time = test_all_samples(pipe, dataset, log_file, epoch=i)

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