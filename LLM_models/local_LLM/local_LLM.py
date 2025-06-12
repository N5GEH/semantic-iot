from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "NousResearch/Nous-Hermes-2-Mistral-7B"

tokenizer = AutoTokenizer.from_pretrained(model_id)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto", # uses GPU if available
    load_in_4bit=True,
    torch_dtype="auto"  # float16 or bfloat16 if supported
)
