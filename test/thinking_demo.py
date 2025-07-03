
import textwrap
from semantic_iot.utils.tools import execute_tool, FILE_ACCESS, CONTEXT, VALIDATION, RML_ENGINE, SIOT_TOOLS
from semantic_iot.utils import LLMAgent, models
from semantic_iot.utils.prompts import prompts

# Need to PRESERVE thinking blocks!!! OR interleaved thinking with Claude 4
# https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#extended-thinking-with-tool-usehttps://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#extended-thinking-with-tool-use

system_prompt = """
# Thinking behavior
Think in triples: subject, predicate, object.
# Use the thinking tags to provide reasoning for your answers.
Example:
Prompt: What is the capital of France?
Thinking: <thinking>[subject: France, predicate: hasCapital, object: Paris]</thinking>
"""

system_prompt = prompts.cot_extraction

prompt = f"Task: Complete: 1, 2, 4, 8, ..."

# prompt = "What is text in uppercase"

# {prompts.cot_extraction}

claude = LLMAgent(system_prompt=system_prompt, model="4sonnet", result_folder="temp")
claude.query(
    prompt=prompt,
    thinking=True,
    temperature=0.0,
    stop_sequences=[],
)