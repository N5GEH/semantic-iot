from semantic_iot.claude import ClaudeAPIProcessor
claude = ClaudeAPIProcessor(api_key="", use_api=True)

response = claude.query("do you know what data format a get request from the openhub IoT platform is? from where do you have the information? do you understand the information?", step_name="test")

result = response["content"][0]["text"]

# print(response)
print(result)