import time
from datetime import datetime
import requests
import json
import anthropic
from typing import Dict, Any, List, Optional, Union
from memory_profiler import memory_usage

from pathlib import Path
root_path = Path(__file__).parent
print(f"Root path: {root_path}")

# Import the tools module
try:
    from semantic_iot.tools import get_tool, get_tools, execute_tool
except ImportError:
    from tools import get_tool, get_tools, execute_tool
import re


# py -m pip install .

class ClaudeAPIProcessor:    
    def __init__(self, 
                 api_key: str = "", 
                 model: str = "claude-3-7-sonnet-20250219", 
                 use_api: bool = True, 
                 temperature: float = 1.0,
                 tool_names: Optional[List[str]] = None):
        """
        Initialize the Claude API processor

        Args:
            api_key: Your Anthropic API key
            model: Claude model to use
            use_api: Whether to use the API or not
            temperature: Temperature parameter for Claude
            tool_names: Names of tools to make available to Claude
        """
        # Get API key
        self.use_api = use_api
        if self.use_api:
            if api_key:
                self.api_key = api_key
            else:
                try:
                    with open(f"{root_path}/ANTHROPIC_API_KEY", "r") as f:
                        self.api_key = f.read().strip()
                except FileNotFoundError:
                    self.api_key = input(f"Couldn't find API key in {root_path}/ANTHROPIC_API_KEY\nEnter your Anthropic API key: ")
        
        else: 
            print("API not used")
            return


        self.model = model
        self.temperature = temperature
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        self.conversation_history = []

        self.step_results = {}
        self.metrics = {}
        
        # Store tool names and get tool definitions if provided
        self.tool_names = tool_names
        self.tools = get_tools(tool_names) if tool_names else []

    def query(self,
                    prompt: str,
                    step_name: str = 0,
                    max_retry: int = 5,
                    conversation_history = None,
                    temperature: float = None,
                    thinking: bool = False,
                    use_tools: bool = False) -> Dict[str, Any]:
        """
        Send a query to Claude API

        Args:
            prompt: The prompt to send to Claude
            step_name: The name of the step
            max_retry: Maximum number of retries in case of a 429 error
            conversation_history: Optional conversation history to use for this query
            temperature: Optional temperature parameter to override the instance setting
            thinking: Enable thinking mode if the model supports it
            use_tools: Whether to use tools in this query

        Returns:
            The JSON response from Claude
        """    
        
        # Check if API is used
        if not self.use_api:
            print("Prompt:")
            print(prompt)
            response = input("Enter the response: ")
            result = {
                "content": [
                    {
                        "text": response
                    }
                ],
                "usage": {
                    "output_tokens": len(response),
                    "input_tokens": len(prompt)    
                }
            }
            return result
        
        print (f"✨ Generating with Claude... ({step_name})")
        

        # Get temperature from instance or use provided temperature
        if temperature is None:
            temperature = self.temperature
        else:
            self.temperature = temperature
        
        # Use provided conversation history or the instance's history
        messages = conversation_history if conversation_history \
            else self.conversation_history.copy()

        # Add user message to messages
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 20000,
            "system": "You are an expert in engineering who is specialized in developing knowledge graphps for building automation with IoT platforms. Be precise and concise.", # TODO make it not generically but as a parameter in the constructor?
            "temperature": self.temperature # "top_p": 1.0
        }

        # Add thinking parameter only if thinking is set to True
        if thinking:
            data["thinking"] = {
                "type": "enabled",
                "budget_tokens": 16000
            }
            
        # Add tools if available and requested
        if use_tools and self.tools:
            data["tools"] = self.tools

        result = None
        for i in range(max_retry):
            start_time = time.time()
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(data)
            )
            end_time = time.time()
            if response.status_code == 200: # Request successful
                result = response.json()
                break
            elif response.status_code == 429: # Too many requests
                if i < max_retry - 1:
                    print(f"Received 429 error: Too many requests. Retrying... ({i + 1}/{max_retry})")
                    time.sleep(61)
                    continue
                else:
                    print(f"Error: {response.status_code}")
                    print(response.text)
                    raise Exception("Max retries reached. "
                                    "API request failed with status code 429")
                
            elif response.status_code == 529: # The service is overloaded
                raise Exception(f"⌚ API is temporarily overloaded, try again later")
                
    
            else:
                print(f"Error: {response.status_code}")
                print(response.text)

                raise Exception(f"API request failed with "
                                f"status code {response.status_code}")        # Use streaming for tool calls if we have tools available
        if use_tools and self.tools:
            # Create an Anthropic client
            client = anthropic.Anthropic(api_key=self.api_key)
            
            print(f"\nStarting streaming request with tools...")
            
            # Convert our messages format to Anthropic's format
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
              # Start streaming with tools
            try:
                with client.messages.stream(
                    model=self.model,
                    max_tokens=20000,
                    system="You are an expert in engineering who is specialized in developing knowledge graphps for building automation with IoT platforms. Be precise and concise.",
                    messages=formatted_messages,
                    tools=self.tools,
                    temperature=temperature
                ) as stream:
                    message_content = []
                    response_text = ""
                    thinking_text = None
                    
                    # Process the stream
                    for text in stream.text_stream:
                        print(text, end="", flush=True)
                        response_text += text
                        
                    # Check for tool calls in the message
                    if stream.message.tool_calls:
                        for tool_call in stream.message.tool_calls:
                            # Claude wants to use a tool
                            print(f"\n\nClaude wants to use the {tool_call.name} tool:")
                            print(f"Input: {json.dumps(tool_call.input, indent=2)}")
                            
                            try:
                                # Execute the tool
                                tool_result = execute_tool(tool_call.name, tool_call.input)
                                print(f"Tool result: {json.dumps(tool_result, indent=2)}")
                                
                                # Send the tool output back to Claude
                                # Define the tool outputs to send
                                tool_outputs = [{
                                    "tool_call_id": tool_call.id,
                                    "output": tool_result
                                }]
                                
                                # Create a new stream with the tool outputs
                                with client.messages.stream(
                                    model=self.model,
                                    max_tokens=20000,
                                    system="You are an expert in engineering who is specialized in developing knowledge graphps for building automation with IoT platforms. Be precise and concise.",
                                    messages=formatted_messages + [
                                        {"role": "assistant", "content": [{"type": "text", "text": response_text}], "tool_calls": [tool_call.model_dump()]}
                                    ],
                                    tool_outputs=tool_outputs,
                                    tools=self.tools,
                                    temperature=temperature
                                ) as tool_stream:
                                    # Continue the conversation with the tool outputs
                                    response_text = ""
                                    for text in tool_stream.text_stream:
                                        print(text, end="", flush=True)
                                        response_text += text
                            except Exception as e:
                                print(f"Error executing tool: {str(e)}")
                                # Continue without tool results if there was an error
                      # Create a result object compatible with the rest of the code
                    result = {
                        "content": [{"text": response_text}],
                        "usage": {
                            "input_tokens": 0,  # These will be estimated
                            "output_tokens": 0  # These will be estimated
                        }
                    }
                    
                    # Check if thinking is available in the message response
                    if hasattr(stream.message, "thinking") and stream.message.thinking:
                        thinking_text = stream.message.thinking
                        result["content"].append({
                            "type": "thinking",
                            "thinking": thinking_text
                        })
                    
                    print("\nStreaming completed")
            
            except Exception as e:
                print(f"Error in streaming: {str(e)}")
                # Fall back to non-streaming approach
                print("Falling back to non-streaming approach...")
                # Continue with the original non-streaming code below
                return self.query(
                    prompt=prompt,
                    step_name=step_name,
                    max_retry=max_retry,
                    conversation_history=conversation_history,
                    temperature=temperature,
                    thinking=thinking,
                    use_tools=False  # Disable tools to prevent infinite recursion
                )
        
        # Process thinking content if present
        thinking_text = None
        response_text = None
        
        if result and "content" in result:
            for block in result["content"]:
                if "type" in block and block["type"] == "thinking" and "thinking" in block:
                    thinking_text = block["thinking"]
                elif "type" in block and block["type"] == "text" and "text" in block:
                    response_text = block["text"]
                # For backwards compatibility with older API responses
                elif "text" in block:
                    response_text = block["text"]

        # If no structured content types found, fallback to first content block
        if response_text is None and result and "content" in result and len(result["content"]) > 0:
            # Handle case where response doesn't use the structured format
            if "text" in result["content"][0]:
                response_text = result["content"][0]["text"]
        
        # Add assistant response to the provided messages list
        if response_text:
            messages.append({
                "role": "assistant",
                "content": response_text
            })

        # Save the step results
        self.step_results[step_name] = {
            "prompt": prompt,
            "response": response_text
        }
            
        # Update instance conversation history if using it
        if not conversation_history:
            self.conversation_history = messages        # Store metrics - handle streaming case where tokens may not be available
        



        # METRICS        

        self.metrics[step_name] = {
            "goal": None,
            "thinking": None,
            "performance": {
                "time_seconds": None,
                "tokens": {
                    "input_tokens": None,
                    "output_tokens": None
                },
                "memory": None
            },
            "evaluation": None,
        }

        # Extract goal text between <goal> and </goal> if present
        match = re.search(r"<goal>(.*?)</goal>", prompt, re.DOTALL)
        goal = match.group(1).strip() if match else prompt

        # Extract instructions if present
        match = re.search(r"<instructions>(.*?)</instructions>", prompt, re.DOTALL)
        instructions = match.group(1).strip() if match else prompt

        # Save goal text if available
        if goal:
            self.metrics[step_name]["goal"] = goal
        else: 
            self.metrics[step_name]["goal"] = prompt

        # Save thinking text if available
        if thinking_text:
            self.step_results[step_name]["thinking"] = thinking_text
            self.metrics[step_name]["thinking"] = thinking_text
        else:
            self.metrics[step_name]["thinking"] = instructions

        # Add timing information to metrics
        elapsed_time = end_time - start_time
        self.metrics[step_name]["performance"]["time_seconds"] = elapsed_time
        print(f"⌛ Query time: {elapsed_time:.2f} seconds")

        # Get token usage metrics
        try:
            self.metrics[step_name]["performance"]["tokens"] = result.get("usage", {})
            self.metrics[step_name]["performance"]["input_tokens"] = result.get("usage", {}).get("input_tokens", 0)
            self.metrics[step_name]["performance"]["output_tokens"] = result.get("usage", {}).get("output_tokens", 0)
        except (KeyError, TypeError): # If token counts aren't available (like in streaming), estimate them
            print("⚠️ Warning: Token counts not available in the response. Estimating...")
            self.metrics[step_name]["performance"]["tokens"] = {}
            self.metrics[step_name]["performance"]["input_tokens"] = len(prompt) // 4  # Rough estimate
            self.metrics[step_name]["performance"]["output_tokens"] = len(response_text) // 4  # Rough estimate
        
        return response_text
    
    def regenerate (self, error_message) -> None:
        '''
        Correct generated content based on error messages.
        '''
        
        prompt = f"""
            The goal of this prompt is the same as the previous one. Now consider the error message.

            ERROR MESSAGE:
            {error_message}
        """
        
        response = self.query(prompt)

        # tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        # self.used_tokens.append(tokens)

        print("PROMPT: \n", prompt)
        print("DATA: \n", response)
        # print("TOKENS: ", tokens)

        return response


    def save_results(self, output_file: str) -> None:
        """
        Save the pipeline results to a JSON file

        Args:
            output_file: Path to the output JSON file
        """
        with open(output_file, 'w') as f:
            json.dump(self.step_results, f, indent=2)

        print(f"\nResults saved to {output_file}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the metrics of the pipeline

        Returns:
            The metrics of the pipeline
        """
        print(f"📐 Metrics: {self.metrics}")
        return self.metrics

