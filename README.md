# Fixing Code Generation Errors for Large Language Models
This replication package contains three .py files: postprocessing.py, modules_db.py, ChatGPT.py

- `postprocessing.py`: Integrates four repair solutions proposed in the paper, tests the model, and is applicable to open-source models on Hugging Face.
- `modules_db.py`: A simple database built based on commonly used modules and functions in the model.
- `ChatGPT.py`: Test code written for the proprietary model GPT-3.5-turbo.

---

For open-source models on Hugging Face, you can create a new .py file in the current directory and test it with the following code (as an example of testing the model Phi-1 ten times) :

```python
import postprocessing
import torch
from datasets import load_dataset
from transformers import pipeline

pipe = pipeline("text-generation", model="microsoft/phi-1", trust_remote_code=True, device_map="auto",
                torch_dtype=torch.bfloat16)

dataset = load_dataset("openai_humaneval")

file = open('output/test-Phi-1-1.3B.txt', mode='w', encoding='utf-8')
postprocessing.test_multiple_times(pipe, dataset, file, 10)
```

For GPT-3.5-turbo, you should replace the value of `openai.api_key` with your own key, and decide whether to use a proxy based on your network situation (modify `openai.proxy`), then simply run `ChatGPT.py` directly.
