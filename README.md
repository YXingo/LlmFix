# LlmFix

## src

- `LlmFix.py`: Contains various functions for testing open-source models on Hugging Face or GPT-3.5-turbo. You can choose to apply the fix solutions proposed in the paper to test the models.
- `modules_db.py, modules.json`: A simple database built based on commonly used modules and functions in the model.
- `ChatGPT.py`: A simple wrapper for various OpenAI models.

---

Test the **codellama-python-7b** model on the **HumanEval** dataset and output the results:

```bash
python3 humaneval-codellama-python-7b.py
```

Test the **codellama-python-7b** model on the **MBPP** dataset and output the results:

```bash
python3 mbpp-codellama-python-7b.py
```

Test the **gpt-3.5-turbo** model on the **HumanEval** dataset and output the results (you need to **fill in your own API key**):

```bash
python3 humaneval-gpt-3.5-turbo.py
```

Test the **gpt-3.5-turbo** model on the **MBPP** dataset and output the results (you need to **fill in your own API key**):

```bash
python3 mbpp-gpt-3.5-turbo.py
```

If you want to test other models, you will need to modify the code in the corresponding files.

## datasets

This folder contains all the datasets used in the paper.
