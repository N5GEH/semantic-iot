import sys
from pathlib import Path
import json
sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path

from semantic_iot.utils import ClaudeAPIProcessor
from semantic_iot.utils.prompts import prompts

METRICS = "LLM_models\metrics\metrics.json"
METRIC_ONE_PATH = "LLM_models\metrics\metrics_I_example.json"
METRIC_TWO_PATH = "LLM_models\metrics\metrics_II_example.json"
METRIC_THREE_PATH = "LLM_models\metrics\metrics_III_example.json"

def load_metrics(metric_path):
    with open(metric_path, 'r') as file:
        content = json.load(file)
    return content

def get_total_performance(metrics):
    """
    Calculate the sum of tokens from the metrics.
    """
    input_token_sum = 0
    output_token_sum = 0
    token_sum = 0
    time_sum = 0

    for step in metrics.values():
        performance = step.get("performance", {})
        input_tokens = performance.get("tokens", {}).get("input_tokens", 0)
        output_tokens = performance.get("tokens", {}).get("output_tokens", 0)
        time_seconds = performance.get("time", {}).get("latency", 0)

        input_token_sum += input_tokens
        output_token_sum += output_tokens
        token_sum += input_tokens + output_tokens
        time_sum += time_seconds

    return f"""Input Tokens: {input_token_sum}, 
        Output Tokens: {output_token_sum}, 
        Token Sum: {token_sum}
        Total Time: {time_sum} s
    """

def get_token_per_steps(metrics):
    """
    Get the token count for each step in the metrics, sorted by token count descending.
    Returns a dictionary with the step key as key and the token count as value.
    """
    token_dict = {}
    for key, step in metrics.items():
        performance = step.get("performance", {})
        input_tokens = performance.get("tokens", {}).get("input_tokens", 0)
        output_tokens = performance.get("tokens", {}).get("output_tokens", 0)
        token_count = input_tokens + output_tokens
        token_dict[key] = f"in: {input_tokens}, out: {output_tokens}, sum: {token_count}" # token_count
    return json.dumps(token_dict, indent=4)
    # Sort by token count descending
    sorted_token_dict = dict(sorted(token_dict.items(), key=lambda item: item[1], reverse=True))
    return json.dumps(sorted_token_dict, indent=4)

def get_len_of_thinking_per_steps(metrics):
    """
    Get the length of the 'thinking' text for each step in the metrics.
    Returns a dictionary with the step key as key and the length of the thinking text as value.
    """
    thinking_dict = {}
    for key, step in metrics.items():
        thinking = step.get("thinking")
        if thinking is not None and thinking != "No Thinking":
            thinking_length = len(thinking.split())
            thinking_dict[key] = thinking_length
    return json.dumps(thinking_dict, indent=4)

def extract_thinking(metrics):
    """
    Extract the 'thinking' text from each step in the metrics.
    Returns a single string concatenating all thinking texts, separated by newlines.
    """
    thinkings = []
    for step in metrics.values():
        thinking = step.get("thinking")
        if thinking is not None and thinking != "No Thinking":
            thinkings.append(thinking)
    return "\n".join(thinkings)

def forget_find_match_steps(metrics):
    """
    Remove steps whose keys start with 'find_match' from a metrics dictionary.
    If metrics is a JSON string, parse it to a dictionary first.
    """
    if isinstance(metrics, str):
        import json
        metrics = json.loads(metrics)
    return {k: v for k, v in metrics.items() if not k.startswith("find_match")}


def get_sum_cached_read_tokens(metrics):
    """
    Calculate the sum of cache_read_input_tokens from the metrics.
    """
    total = 0
    for step in metrics.values():
        performance = step.get("performance", {})
        tokens = performance.get("tokens", {})
        total += tokens.get("cache_read_input_tokens", 0)
    return total

def split_in_steps(metrics):
    """
    Split the metrics into steps.
    """
    # Placeholder for splitting logic
    pass

def compare_steps(metrics):
    """
    Compare the steps in the metrics.
    """
    # Placeholder for comparison logic
    pass







if __name__ == "__main__":

    metric_paths = {
        "0": METRICS,
        # "I": METRIC_ONE_PATH,
        # "II": METRIC_TWO_PATH,
        # "III": METRIC_THREE_PATH
    }

    metrics = {}
    total_performance = {}
    tokens_per_step = {}
    thinking_length = {}
    thinking_text = {}
    cached_read_tokens = {}

    for key, path in metric_paths.items():
        m = load_metrics(path)
        metrics[key] = m
        total_performance[key] = get_total_performance(m)
        tokens_per_step[key] = get_token_per_steps(m)
        thinking_length[key] = get_len_of_thinking_per_steps(m)
        thinking_text[key] = extract_thinking(forget_find_match_steps(m))
        cached_read_tokens[key] = get_sum_cached_read_tokens(m)

    for key in metric_paths:
        print(f"Token sum for metric {key}: {total_performance[key]}")
        print(f"Token per step for metric {key}: \n{tokens_per_step[key]}")
        print(f"Thinking length for metric {key}: \n{thinking_length[key]}")
        print(f"Sum of cached read tokens for metric {key}: {cached_read_tokens[key]}")

    # print (f"Thinking for metric I: \n{m1_thinking}")
    # print (f"Thinking for metric II: \n{m2_thinking}")

    input("Continue? (y/n): ")

    system = """
    You are an expert in evaluating the effort required for a an expert in engineering who is specialized in developing knowledge graphps 
    for building automation with IoT platforms to perform tasks.
    """
    

    claude = ClaudeAPIProcessor(system_prompt=system)

    prompt = f"""

    <data>
    Task 1: 
    {thinking_text["I"]}

    Task 2:
    {thinking_text["II"]}
    </data>

    In a first step, evaluate the following metrics for each task on a scale from 1 to 100 (1 = minimal human effort, 100 = maximal human effort):
    {prompts.human_effort_metrics}

    In a second step, based on the individual metrics:
    Compare the effort an expert in engineering who is specialized in developing knowledge graphps 
    for building automation with IoT platforms would need to do the tasks. 
    Important are not the absolute values but the relative proportions between the steps.

    Which task is easier to do? How much? Why?

    """
    # TODO turn into two queries, return the CoT of first step as input for the second

    response = claude.query(prompt, step_name="compare_steps", tools="")
    # print(f"Claude response: {response}")

output = """
    Return a JSON object where you put all generated effort scores 
    within the evaluation section in the same hierarchical structure:

    {{
        "step_name": {{
            "evaluation": {{
                
            }}
        }}
    }}
"""




#############

# Example Response::
"""
## Task 1: JSON Analysis & Configuration Creation

### Difficulty Metrics:
- **Thinking Quantity**: High (8/10) - Requires multiple analytical steps: identifying JSON structure patterns, extracting entity identifiers, determining properties for extra nodes, understanding API structure, and verifying ontology mappings.
- **Thinking Complexity**: High (7/10) - Involves pattern recognition, JSONPath expression formulation, and mapping concepts across different domains.
- **Decision Quantity**: High (8/10) - Many decisions about identifiers, property modeling, platform identification, and term mappings.
- **Decision Complexity**: Medium-High (7/10) - Several options for each decision point, especially for ontology mappings.
- **Knowledge Prerequisites**: Medium-High (7/10) - Requires understanding of JSON structures, knowledge graphs, Brick ontology, and FIWARE platform.
- **Working Memory Load**: High (8/10) - Needs to track JSON structures, mapping relationships, and configuration requirements simultaneously.

### Estimation:
- **Duration**: 3-4 hours
- **Cognitive Load**: High (8/10)
- **Error Potential**: Medium (6/10) - Multiple steps increase error chances, but errors are generally detectable through validation.

## Task 2: RML Mapping Generation

### Difficulty Metrics:
- **Thinking Quantity**: Medium-High (7/10) - Focused on RML mapping creation steps.
- **Thinking Complexity**: Very High (9/10) - RML requires sophisticated transformation logic between JSON and RDF.
- **Decision Quantity**: Medium (6/10) - Decisions primarily concern mapping approaches.
- **Decision Complexity**: Medium-High (7/10) - Several ways to implement each mapping.
- **Knowledge Prerequisites**: Very High (9/10) - Requires specialized knowledge of RML syntax, RDF concepts, and triple structure formation.
- **Working Memory Load**: Very High (9/10) - Must simultaneously track JSON structure, ontology relationships, and RML syntax rules.

### Estimation:
- **Duration**: 2-3 hours (focused but intensive)
- **Cognitive Load**: Very High (9/10)
- **Error Potential**: High (8/10) - RML syntax is precise and error-prone, with errors often only detectable during execution.

# Comparison of Effort

Task 2 (RML Mapping Generation) is moderately more difficult than Task 1, primarily because:

1. **Specialized Knowledge Requirements**: RML is a specialized language with strict syntax requirements that few engineers have mastered. While Task 1 requires breadth of knowledge, Task 2 requires deeper technical expertise in a specific area.

2. **Cognitive Complexity**: Transforming between data models (JSON to RDF) involves more complex cognitive operations than analyzing and configuring JSON structures.

3. **Error Potential**: RML mappings have higher error potential because:
   - Syntax errors can be difficult to debug
   - Logical mapping errors might only appear during execution
   - Testing requires complete pipeline implementation

4. **Knowledge Graph Specificity**: Task 2 more directly involves the core specialty of "developing knowledge graphs for building automation" as it involves the actual transformation to RDF, while Task 1 is more preparatory.

An expert in knowledge graphs for building automation would likely find Task 1 more straightforward because it leverages broader skills in data analysis and configuration, while Task 2 requires the specialized RML knowledge that even experienced knowledge graph engineers might not use regularly.

"""





# Example Metric file:

metric = {
    "default_step_(1)": {
        "step_name": "default_step_(1)",
        "prompt": "How do I access a sensor value from the FIWARE API?",
        "thinking": "The user wants to know how to access a sensor value from the FIWARE API. FIWARE is a platform for smart city and IoT applications, so this is relevant to my expertise in knowledge graphs for building automation with IoT platforms.\n\nTo properly help the user, I should check if we have information about FIWARE API specifications. I'll use the `get_file_paths` function to see what resources are available.\n\nThen, I would need to:\n1. Check if there's an API specification file for FIWARE\n2. Use the specification to determine how to access sensor values\n3. Provide a clear explanation to the user\n\nLet me start by checking the available files.",
        "response": "I'll help you understand how to access sensor values from the FIWARE API. Let me first check if we have API specifications available for FIWARE.",
        "performance": {
            "time": {
                "latency": 5.99,
                "tpot": 0.0264,
                "ttft": None
            },
            "tokens": {
                "input_tokens": 1052,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 227
            }
        }
    },
}