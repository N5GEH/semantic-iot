

from semantic_iot.tools import execute_tool, FILE_ACCESS, CONTEXT, VALIDATION, RML_ENGINE, SIOT_TOOLS

# Need to PRESERVE thinking blocks!!!
# https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#extended-thinking-with-tool-usehttps://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#extended-thinking-with-tool-use

from semantic_iot.utils import ClaudeAPIProcessor, models

claude = ClaudeAPIProcessor(system_prompt="", model="4sonnet")

prompt = """

Task 1: Complete: 1, 2, 5, 14, ...
Task 2: Complete: 1, 2, 4, 7, ...

Think step by step. 
Give the reasoning process in detail in thinking tags.

Which task is easier to complete?
Why?

"""

# TODO just try out with sonnet 4 and compare thinking outputs

claude.query(
    prompt=prompt,
    thinking=True,
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