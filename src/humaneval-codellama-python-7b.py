import LlmFix
import torch
from datasets import load_dataset
from transformers import pipeline

pipe = pipeline("text-generation", model="codellama/CodeLlama-7b-Python-hf", device=0,
                torch_dtype=torch.bfloat16)
dataset = load_dataset("openai_humaneval")
file = open('humaneval-codellama-python-7b.txt', mode='w', encoding='utf-8')

LlmFix.test_multiple_times(pipe, dataset, file, times=10)
