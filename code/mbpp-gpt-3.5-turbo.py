import postprocessing
import openai
from datasets import load_dataset

openai.api_key = "sk-sU3lRQJkjEnjpICkC780BeA787C446DeAeF6Ec98Bb5c39Aa"
openai.api_base = "https://api.kwwai.top/v1"
dataset = load_dataset("gonglinyuan/mbpp_with_prompt")
test_dataset = load_dataset("mbpp")
file = open('mbpp-GPT-3.5-turbo.txt', mode='w', encoding='utf-8')

postprocessing.test_multiple_times(None, dataset, file, times=10, GPT=True, mbpp=True, test_dataset=test_dataset)
