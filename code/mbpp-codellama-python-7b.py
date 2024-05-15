import postprocessing
import torch
from datasets import load_dataset
from transformers import pipeline

pipe = pipeline("text-generation", model="codellama/CodeLlama-7b-Python-hf", device=0,
                torch_dtype=torch.bfloat16)
dataset = load_dataset("gonglinyuan/mbpp_with_prompt")
test_dataset = load_dataset("mbpp")
file = open('mbpp-codellama-python-7b.txt', mode='w', encoding='utf-8')

postprocessing.test_multiple_times(pipe, dataset, file, times=10, mbpp=True, test_dataset=test_dataset)
