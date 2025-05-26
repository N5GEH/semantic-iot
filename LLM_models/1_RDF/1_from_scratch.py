
from semantic_iot.utils.prompts import prompt_I, prompt_II, prompt_III

target = """
- In this case, the IoT platform is: FIWARE.
- The target JSON data is: "LLM_models/datasets/fiware_v1_hotel/fiware_entities_2rooms.json"
"""

prompt = prompt_I.format(target=target)

print(prompt)

input("Press Enter to continue...")


from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from semantic_iot.claude import ClaudeAPIProcessor

claude = ClaudeAPIProcessor()
# response = claude.query(prompt_I, step_name="scenario_I", tools="I")
response = claude.query(prompt, step_name="scenario_II", tools="II")