# Fixing Code Generation Errors for Large Language Models

## code

This folder contains four files: `postprocessing.py, modules_db.py, modules.json, ChatGPT.py`

- `postprocessing.py`: Contains various functions for testing open-source models on Hugging Face or GPT-3.5-turbo. You can choose to apply the fix solutions proposed in the paper to test the models.
- `modules_db.py, modules.json`: A simple database built based on commonly used modules and functions in the model.
- `ChatGPT.py`: A simple wrapper for various OpenAI models.

---

For open-source models on Hugging Face (such as CodeLlama-Python-7B) , you can test it with the following code:

```python
import postprocessing
import torch
from datasets import load_dataset
from transformers import pipeline

pipe = pipeline("text-generation", model="codellama/CodeLlama-7b-Python-hf", device_map='auto', torch_dtype=torch.bfloat16)
dataset = load_dataset("openai_humaneval")

file = open('humaneval-fixed-codellama-python-7B.txt', mode='w', encoding='utf-8')

postprocessing.test_multiple_times(pipe, dataset, file, do_fix=True, times=10)
```

For GPT-3.5-turbo, you should replace the value of `openai.api_key` with your own key, and test it with the following code:

```python
import postprocessing
import openai
from datasets import load_dataset

openai.api_key = "your key"
dataset = load_dataset("openai_humaneval")

file = open('humaneval-fixed-GPT-3.5-turbo.txt', mode='w', encoding='utf-8')

postprocessing.test_multiple_times(None, dataset, file, do_fix=True, times=10, GPT=True)
```

## data

This folder contains all the experimental data presented in the paper.