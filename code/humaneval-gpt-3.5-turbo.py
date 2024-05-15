import postprocessing
import openai
from datasets import load_dataset

openai.api_key = "your key"
dataset = load_dataset("openai_humaneval")
file = open('humaneval-GPT-3.5-turbo.txt', mode='w', encoding='utf-8')

postprocessing.test_multiple_times(None, dataset, file, times=10, GPT=True)
