from semantic_iot.claude import ClaudeAPIProcessor
claude = ClaudeAPIProcessor(api_key="", use_api=True)


prompt = """
do you know what data format a get request from the openhub IoT platform is? from where do you have the information? do you understand the information?
"""

response = claude.query(prompt, step_name="test")
result = response["content"][0]["text"]
tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]

print(tokens)

response = claude.query("What was the last prompt?", step_name="test")
result = response["content"][0]["text"]
tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]

# print(response)
print(result)
print(tokens)