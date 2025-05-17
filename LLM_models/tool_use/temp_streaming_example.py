
import anthropic

with open(r"C:\Users\\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\LLM_models\ANTHROPIC_API_KEY", "r") as f:
    api_key = f.read().strip()

client = anthropic.Anthropic(api_key=api_key)

with client.messages.stream(
    messages=[{"role": "user", "content": "What's the weather in San Francisco?"}],
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    tools=[
        {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        }
    ]
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "tool_use":
                print(f"Using tool: {event.content_block.name}")
                
        elif event.type == "content_block_delta":
            if event.delta.type == "tool_use":
                print(f"Tool input: {event.delta.partial_json}")
