
from datetime import datetime
current_time = datetime.now().strftime("%Y_%m_%d_%H_%M")

from pathlib import Path
project_root_path = Path(__file__).parent.parent # "Code" Folder

from LLM.claude import ClaudeAPIProcessor


processor = ClaudeAPIProcessor()

# result = processor.query_claude(prompt="What is the temperature in the living room?", step_name="1")
# print(result)

PROMPTS = f"{project_root_path}/yannik/LLM/prompts_copy.json"
OUTPUT = f"{project_root_path}/yannik/LLM/output/results.json"

processor.bulk_query(
    prompts_file_path=PROMPTS, 
    output_file_path=OUTPUT)


''' Step Results
{
'id': 'msg_0183XbAzFGc8MXT5fQstNN7C', 
'type': 'message', 
'role': 'assistant', 
'model': 'claude-3-5-sonnet-20241022', 
'content': [{
    'type': 'text', 
    'text': "I am not able to detect the temperature in your living room or any physical location. I don't have access to temperature sensors or real-time environmental data. To check the temperature in your living room, you would need to look at a thermometer or temperature gauge in that room."}], 
    'stop_reason': 'end_turn', 
    'stop_sequence': None, 
    'usage': {
        'input_tokens': 16, 
        'cache_creation_input_tokens': 0, 
        'cache_read_input_tokens': 0, 
        'output_tokens': 60}}'
'''