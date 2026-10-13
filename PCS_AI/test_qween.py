from mlx_lm import load, generate

model_id = "mlx-community/Qwen2.5-14B-Instruct-4bit"

model, tokenizer = load(model_id)

messages = [
    {
        "role": "user",
        "content": (
            "Explain the difference between a new "
            "polynomial commitment scheme and a SNARK "
            "that uses an existing PCS."
        )
    }
]

prompt = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=False
)

response = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=500,
    verbose=False
)

print(response)
