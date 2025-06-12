from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import torch.nn.functional as F
from accelerate import infer_auto_device_map

model_name = "mistralai/Mistral-7B-Instruct-v0.1"

# Better memory management
model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    device_map="auto", 
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,  # Reduces CPU memory usage
    trust_remote_code=True
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# ================ Logits and Log Probabilities Extraction ================
prompt = "1, 2, 4, 8, 1"
inputs = tokenizer(prompt, return_tensors="pt")

# Move inputs to the same device as the model's first parameter
device = next(model.parameters()).device
inputs = {k: v.to(device) for k, v in inputs.items()}

with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits  # shape: (1, seq_len, vocab_size)
    log_probs = F.log_softmax(logits, dim=-1)
    
    # Get top predictions for the last token
    last_token_logits = logits[0, -1, :]
    top_k_values, top_k_indices = torch.topk(last_token_logits, 5)
    top_k_tokens = [tokenizer.decode(idx) for idx in top_k_indices]
    
    print("Top 5 predictions:")
    for token, score in zip(top_k_tokens, top_k_values):
        print(f"- {score.item():.2f}: {token}")

# ================ Attention Weights Extraction ================
attn_data = []

def attn_hook(module, input, output):
    # Handle different output formats
    if isinstance(output, tuple) and len(output) > 1:
        attn_weights = output[1]  # attention weights
        if attn_weights is not None:
            attn_data.append(attn_weights.cpu())  # Move to CPU to save GPU memory

# Clear previous hooks
for layer in model.model.layers:
    layer.self_attn._forward_hooks.clear()

# Register hooks for attention extraction
handles = []
for layer in model.model.layers:
    handle = layer.self_attn.register_forward_hook(attn_hook)
    handles.append(handle)

# Forward pass with attention extraction
with torch.no_grad():
    outputs = model(**inputs, output_attentions=True)  # Explicitly request attentions

print(f"Collected attention from {len(attn_data)} layers")

# Clean up hooks
for handle in handles:
    handle.remove()

# ================ Memory Cleanup ================
torch.cuda.empty_cache() if torch.cuda.is_available() else None


