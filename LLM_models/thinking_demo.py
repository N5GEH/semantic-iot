
from semantic_iot.tools import execute_tool, FILE_ACCESS, CONTEXT, VALIDATION, RML_ENGINE, SIOT_TOOLS
from semantic_iot.utils import ClaudeAPIProcessor, models
from semantic_iot.utils.prompts import prompts

# TODO Need to PRESERVE thinking blocks!!!
# https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#extended-thinking-with-tool-usehttps://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#extended-thinking-with-tool-use

system_prompt = """
# Thinking behavior
Think in triples: subject, predicate, object.
# Use the thinking tags to provide reasoning for your answers.
Example:
Prompt: What is the capital of France?
Thinking: <thinking>[subject: France, predicate: hasCapital, object: Paris]</thinking>
"""
system_prompt="" # prompts.cot_extraction

prompt = f"""
Task: Complete: 1, 2, 5, 14, ...

<instructions>
Do the task step by step.
Output the thinking process as detailed as possible.
It is really important to output every little step of your reasoning, even if it seems obvious.

Each step, no matter how small, should be classifiable by the bloom taxonomy scale.
Each step, no matter how small, must be outputted as a JSON object with the following keys:
- step: the step number
- bloom: bloom taxonomy level
- number_of_decisions: the number of decisions that need to be made in this step
- number_of_options: the number of options that need to be considered in this step
- human_effort: own evaluation of the human effort required to complete this step (from 1 to 10, where 1 is very easy and 10 is very hard)

Bloom Taxonomy for reference:
- 1: Remembering: Recalling information
- 2: Understanding: Explaining ideas or concepts
- 3: Applying: Using information in new situations
- 4: Analyzing: Breaking information into parts to explore understandings and relationships
- 5: Evaluating: Justifying a decision or course of action
- 6: Creating: Producing new or original work

</instructions>

<output>
Put the answer to the question in output tags and
output the thinking process in thinking tags.
</output>


"""
# {prompts.cot_extraction}

claude = ClaudeAPIProcessor(system_prompt=system_prompt, model="3.7sonnet")
claude.query(
    prompt=prompt,
    thinking=True,
    temperature=0.0,
)