from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import json

"""
SCRAPE:
    Attention weights
    Forward hooks
    Layer activations
    Custom fine-tuning
"""

model_name = "mistralai/Mistral-7B-Instruct-v0.1"

model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    device_map="auto", 
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
    attn_implementation="eager"
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# ================ Task Difficulty Measurement System ================
class TaskDifficultyAnalyzer:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.layer_activations = []
        self.attention_weights = []
        self.layer_gradients = []
        self.entropy_scores = []
        self.confidence_scores = []
        
    def reset_metrics(self):
        """Reset all collected metrics"""
        self.layer_activations.clear()
        self.attention_weights.clear()
        self.layer_gradients.clear()
        self.entropy_scores.clear()
        self.confidence_scores.clear()
    
    def activation_hook(self, layer_idx):
        """Hook to capture layer activations"""
        def hook(module, input, output):
            # Capture hidden states (activations)
            if isinstance(output, tuple):
                hidden_states = output[0]  # First element is usually hidden states
            else:
                hidden_states = output
            
            # Calculate activation statistics
            activation_stats = {
                'layer': layer_idx,
                'mean_activation': hidden_states.mean().cpu().item(),
                'std_activation': hidden_states.std().cpu().item(),
                'max_activation': hidden_states.max().cpu().item(),
                'min_activation': hidden_states.min().cpu().item(),
                'activation_norm': torch.norm(hidden_states).cpu().item(),
                'sparsity': (hidden_states.abs() < 0.01).float().mean().cpu().item()
            }
            self.layer_activations.append(activation_stats)
        return hook
    def attention_hook(self, layer_idx):
        """Hook to capture attention patterns"""
        def hook(module, input, output):
            # print(f"    Attention hook called for layer {layer_idx}")
            if isinstance(output, tuple) and len(output) > 1:
                attn_weights = output[1]  # Attention weights
                if attn_weights is not None:
                    # print(f"    Attention weights shape: {attn_weights.shape}")
                    # Ensure weights are properly normalized (should sum to 1)
                    attn_weights = F.softmax(attn_weights.float(), dim=-1)
                    
                    # Calculate attention entropy (measure of focus)
                    attn_entropy = -torch.sum(attn_weights * torch.log(attn_weights + 1e-9), dim=-1)
                    
                    attention_stats = {
                        'layer': layer_idx,
                        'mean_entropy': attn_entropy.mean().cpu().item(),
                        'max_entropy': attn_entropy.max().cpu().item(),
                        'attention_concentration': (attn_weights.max(dim=-1)[0]).mean().cpu().item(),
                        'attention_spread': attn_weights.std(dim=-1).mean().cpu().item()
                    }
                    self.attention_weights.append(attention_stats)
                    # print(f"    Captured attention stats: entropy={attention_stats['mean_entropy']:.3f}")
                else:
                    print(f"    No attention weights for layer {layer_idx}")
            else:
                print(f"    Unexpected output format for layer {layer_idx}: {type(output)}")
        return hook
    
    def register_hooks(self):
        """Register all hooks for analysis"""
        handles = []
        
        # Register activation hooks for each layer
        for i, layer in enumerate(self.model.model.layers):
            # Hook for hidden states (activations)
            handle1 = layer.register_forward_hook(self.activation_hook(i))
            handles.append(handle1)
            
            # Hook for attention weights
            handle2 = layer.self_attn.register_forward_hook(self.attention_hook(i))
            handles.append(handle2)
        
        return handles
    
    def analyze_task_difficulty(self, prompt, max_new_tokens=10):
        """Analyze task difficulty for a given prompt"""
        self.reset_metrics()
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Register hooks
        handles = self.register_hooks()
        
        generated_response = ""
        
        try:
            with torch.no_grad():
                # Initial forward pass for difficulty analysis
                outputs = self.model(**inputs, output_attentions=True)
                logits = outputs.logits
                
                # Calculate prediction confidence
                probs = F.softmax(logits[0, -1, :], dim=-1)
                top_prob = probs.max().item()
                
                # Convert to float32 for numerical stability in entropy calculation
                probs_f32 = probs.float()  # Convert from float16 to float32
                
                # Debug entropy calculation
                log_probs = torch.log(probs_f32 + 1e-9)
                entropy = -torch.sum(probs_f32 * log_probs).item()
                
                # Handle NaN/inf values
                if np.isnan(entropy) or np.isinf(entropy):
                    print(f"  Warning: Invalid entropy {entropy}, setting to 0")
                    entropy = 0.0
                
                self.confidence_scores.append({
                    'top_probability': top_prob,
                    'entropy': entropy,
                    'perplexity': torch.exp(torch.tensor(entropy)).item()
                })
                
                # Generate actual response from the model
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,  # Use greedy decoding for consistent results
                    pad_token_id=self.tokenizer.eos_token_id,
                    temperature=1.0
                )
                
                # Decode the generated response (excluding the input prompt)
                input_length = inputs['input_ids'].shape[1]
                generated_tokens = generated_ids[0][input_length:]
                generated_response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        finally:
            # Clean up hooks
            for handle in handles:
                handle.remove()
        
        # Compute difficulty metrics and add the generated response
        metrics = self.compute_difficulty_metrics()
        metrics['generated_response'] = generated_response.strip()
        
        return metrics
    def compute_difficulty_metrics(self):
        """Compute comprehensive difficulty metrics"""
        if not self.layer_activations:
            return {"error": "No data collected"}
        
        # Debug information
        print(f"  Debug: Collected {len(self.layer_activations)} activation records")
        print(f"  Debug: Collected {len(self.attention_weights)} attention records")
        print(f"  Debug: Collected {len(self.confidence_scores)} confidence records")
        
        # Activation-based metrics
        activation_means = [stats['mean_activation'] for stats in self.layer_activations]
        activation_stds = [stats['std_activation'] for stats in self.layer_activations]
        activation_norms = [stats['activation_norm'] for stats in self.layer_activations]
        sparsity_scores = [stats['sparsity'] for stats in self.layer_activations]
        
        # Attention-based metrics
        if self.attention_weights:
            attention_entropies = [stats['mean_entropy'] for stats in self.attention_weights]
            attention_concentrations = [stats['attention_concentration'] for stats in self.attention_weights]
        else:
            attention_entropies = []
            attention_concentrations = []
        
        # Safe calculation functions to avoid NaN
        def safe_std(values):
            if len(values) <= 1:
                return 0.0
            return np.std(values)
        
        def safe_corrcoef(x, y):
            if len(x) <= 1 or len(y) <= 1:
                return 0.0
            try:
                corr_matrix = np.corrcoef(x, y)
                if np.isnan(corr_matrix[0, 1]):
                    return 0.0
                return corr_matrix[0, 1]
            except:
                return 0.0
        
        def safe_mean(values):
            if not values:
                return 0.0
            return np.mean(values)
        
        def safe_entropy(entropy_val):
            if np.isnan(entropy_val) or np.isinf(entropy_val):
                return 0.0
            return entropy_val
        
        # Calculate metrics safely
        activation_variability = safe_std(activation_means)
        activation_progression = safe_corrcoef(range(len(activation_means)), activation_means)
        peak_activation_layer = int(np.argmax(activation_norms)) if activation_norms else 0
        activation_instability = safe_mean(activation_stds)
        
        # Sparsity patterns
        average_sparsity = safe_mean(sparsity_scores)
        sparsity_change = (sparsity_scores[-1] - sparsity_scores[0]) if len(sparsity_scores) > 1 else 0
        
        # Attention patterns
        attention_difficulty = safe_mean(attention_entropies)
        attention_focus = safe_mean(attention_concentrations)
        
        # Prediction confidence
        prediction_confidence = self.confidence_scores[0]['top_probability'] if self.confidence_scores else 0
        prediction_uncertainty = self.confidence_scores[0]['entropy'] if self.confidence_scores else 0
        
        # Debug prints for uncertainty
        if self.confidence_scores:
            print(f"  Debug: Raw entropy from confidence_scores: {self.confidence_scores[0]['entropy']}")
            print(f"  Debug: prediction_uncertainty after assignment: {prediction_uncertainty}")
        else:
            print(f"  Debug: No confidence_scores available")
        
        print(f"  Debug: Final prediction_uncertainty: {prediction_uncertainty}")
        
        # Difficulty indicators
        difficulty_metrics = {
            'overall_difficulty_score': 0,  # Will compute below
            
            # Activation patterns
            'activation_variability': activation_variability,
            'activation_progression': activation_progression,
            'peak_activation_layer': peak_activation_layer,
            'activation_instability': activation_instability,
            
            # Sparsity patterns
            'average_sparsity': average_sparsity,
            'sparsity_change': sparsity_change,
            
            # Attention patterns
            'attention_difficulty': attention_difficulty,
            'attention_focus': attention_focus,
            
            # Prediction confidence
            'prediction_confidence': prediction_confidence,
            'prediction_uncertainty': prediction_uncertainty,
            
            # Layer-wise breakdown
            'layer_activations': self.layer_activations,
            'layer_attention': self.attention_weights
        }
        
        # Compute overall difficulty score safely
        difficulty_score = (
            (1 - prediction_confidence) * 0.3 +  # Low confidence = high difficulty
            prediction_uncertainty * 0.2 +       # High uncertainty = high difficulty
            activation_variability * 0.2 +       # High variability = high difficulty
            attention_difficulty * 0.2 +         # High attention entropy = high difficulty
            activation_instability * 0.1         # High instability = high difficulty
        )
        
        # Ensure no NaN in final score
        if np.isnan(difficulty_score) or np.isinf(difficulty_score):
            difficulty_score = 0.0
        
        difficulty_metrics['overall_difficulty_score'] = difficulty_score

        print(f"\nDifficulty score components:")
        print(f"  - Prediction confidence: {prediction_confidence:.3f}")
        print(f"  - Prediction uncertainty: {prediction_uncertainty:.3f}")
        print(f"  - Activation variability: {activation_variability:.3f}")
        print(f"  - Attention difficulty: {attention_difficulty:.3f}")
        print(f"  - Activation instability: {activation_instability:.3f}")
        print(f"-> Weighted difficulty score: {difficulty_score:.3f}\n")
        

        return difficulty_metrics

# ================ Usage Examples ================
analyzer = TaskDifficultyAnalyzer(model, tokenizer)

# Test different tasks with varying difficulty
test_prompts = [
    "1, 2, 4, 8,",  # Simple pattern
    "The capital of France is",  # Simple factual
    "Solve: 2x + 3 = 7, x =",  # Math problem
    "Complete the sequence: 1, 1, 2, 3, 5, 8,",  # Fibonacci
    "Translate to French: Hello world",  # Translation
]

# test_prompts = ["""
# Available Ontology Classes:
# - Class
#   - Collection
#     - System
#       - Heating_Ventilation_Air_Conditioning_System
#         - Air_System: The equipment, distribution systems and terminals that introduce or exhaust, either collectively or individually, the air into and from the building
#           - Ventilation_Air_System: The equipment, devices, and conduits that handle the introduction and distribution of ventilation air in the building
#   - Equipment
#     - HVAC_Equipment
#       - Air_Handler_Unit: Assembly consisting of sections containing a fan or fans and other necessary equipment to perform one or more of the following functions: circulating, filtration, heating, cooling, heat recovery, humidifying, dehumidifying, and mixing of air. Is usually connected to an air-distribution system.
#       - Air_Plenum: A component of the HVAC the receives air from the air handling 

# Identify the most appropriate ontology class for the domain entity: "FreshAirVentilation"

# Output exclusively the selected class from the options of the available Ontology Classes.
# The selected class must exist in the available Ontology Classes.
# Do not provide an explaination or any other output.
# """
# ]

# test_prompts = [
#     "Write a RDF description for a 'FreshAirVentilation' system using the provided ontology class: brick:Air_Ventilation.",
# ]

# MAPPING CRITERIA: (in order of priority)
# 1. Exact semantic match
# 2. Functional equivalence (same purpose/behavior)
# 3. Hierarchical relationship (parent/child concepts)
# 4. Attribute similarity (same properties/characteristics)

# SPECIAL CONSIDERATIONS:
# - Distinguish locations, air systems, devices, actuation points, sensors
# - Avoid category errors: don't confuse the thing itself with infrastructure that supports the thing
# - Respect system hierarchies (building → floor → room → equipment)
# </instructions>


print("=== TASK DIFFICULTY ANALYSIS ===\n")

results = {}
for prompt in test_prompts:
    print(f"Analyzing: '{prompt}'")
    metrics = analyzer.analyze_task_difficulty(prompt)
    results[prompt] = metrics
    
    print(f"  Generated Response: '{metrics.get('generated_response', 'N/A')}'")
    print(f"  Difficulty Score: {metrics['overall_difficulty_score']:.3f}")
    print(f"  Confidence: {metrics['prediction_confidence']:.3f}")
    print(f"  Uncertainty: {metrics['prediction_uncertainty']:.3f}")
    print(f"  Peak Activity Layer: {metrics['peak_activation_layer']}")
    print(f"  Activation Variability: {metrics['activation_variability']:.6f}")
    print("  " + "-"*50)

# ================ Visualization Functions ================
def visualize_layer_activity(metrics, prompt_name):
    """Visualize where the model is 'thinking' across layers"""
    activations = metrics['layer_activations']
    
    layers = [stats['layer'] for stats in activations]
    activation_norms = [stats['activation_norm'] for stats in activations]
    sparsity = [stats['sparsity'] for stats in activations]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot activation strength
    ax1.plot(layers, activation_norms, 'b-', linewidth=2, label='Activation Norm')
    ax1.set_xlabel('Layer')
    ax1.set_ylabel('Activation Strength')
    ax1.set_title(f'Layer Activity for: {prompt_name}')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot sparsity
    ax2.plot(layers, sparsity, 'r-', linewidth=2, label='Sparsity')
    ax2.set_xlabel('Layer')
    ax2.set_ylabel('Sparsity (fraction of near-zero activations)')
    ax2.set_title('Neural Sparsity Across Layers')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(f'layer_activity_{prompt_name.replace(" ", "_")}.png', dpi=300, bbox_inches='tight')
    plt.show()

# Generate visualizations for the most and least difficult tasks
sorted_results = sorted(results.items(), key=lambda x: x[1]['overall_difficulty_score'])
easiest_task = sorted_results[0]
hardest_task = sorted_results[-1]

print(f"\nEasiest Task: '{easiest_task[0]}' (Score: {easiest_task[1]['overall_difficulty_score']:.3f})")
print(f"Hardest Task: '{hardest_task[0]}' (Score: {hardest_task[1]['overall_difficulty_score']:.3f})")

# Uncomment to generate visualizations
# visualize_layer_activity(easiest_task[1], "Easiest_Task")
# visualize_layer_activity(hardest_task[1], "Hardest_Task")

# ================ Simple Test to Verify Fix ================
# print("\n=== TESTING SINGLE PROMPT ===")
# test_prompt = "The capital of France is"
# print(f"Testing: '{test_prompt}'")
# metrics = analyzer.analyze_task_difficulty(test_prompt)

# print(f"Generated Response: '{metrics.get('generated_response', 'N/A')}'")
# print(f"Result keys: {list(metrics.keys())}")
# print(f"Overall difficulty score: {metrics.get('overall_difficulty_score', 'MISSING')}")
# print(f"Prediction confidence: {metrics.get('prediction_confidence', 'MISSING')}")
# print(f"Prediction uncertainty: {metrics.get('prediction_uncertainty', 'MISSING')}")
# print(f"Activation variability: {metrics.get('activation_variability', 'MISSING')}")

# ================ Memory Cleanup ================
torch.cuda.empty_cache() if torch.cuda.is_available() else None