

from semantic_iot.tools import execute_tool, FILE_ACCESS, CONTEXT, VALIDATION, RML_ENGINE, SIOT_TOOLS

# TODO Need to PRESERVE thinking blocks!!!
# https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#extended-thinking-with-tool-usehttps://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#extended-thinking-with-tool-use

from semantic_iot.utils import ClaudeAPIProcessor, models

from semantic_iot.utils.prompts import prompts

system_prompt = """
# Thinking behavior
Think in triples: subject, predicate, object.
# Use the thinking tags to provide reasoning for your answers.
Example:
Prompt: What is the capital of France?
Thinking: <thinking>[subject: France, predicate: hasCapital, object: Paris]</thinking>
"""
system_prompt="" # prompts.cot_extraction

claude = ClaudeAPIProcessor(system_prompt=system_prompt, model="4sonnet")

prompt = f"""

Task 1: Complete: 1, 2, 5, 14, ...
Task 2: Complete: 1, 2, 4, 7, ...

<instructions>
Which task is easier to complete?
</instructions>

<output>
Put the searched Task Number in output tags
</output>

{prompts.cot_extraction}

"""
claude.query(
    prompt=prompt,
    thinking=False,
    temperature=0.0
    # tools="file_access",
    # follow_up=True
)


# for model_name, model in models.items():
#     print(f"Model: {model_name}")
#     claude = ClaudeAPIProcessor(system_prompt="", model=model["api"])
#     response = claude.query(
#         prompt="Complete: 1, 2, 5, 14, ...",
#         thinking=model["thinking"],
#     )