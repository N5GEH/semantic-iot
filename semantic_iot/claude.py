import time
from datetime import datetime
import requests
import json
import re
import anthropic
from typing import Dict, Any, List, Optional, Union
from memory_profiler import memory_usage

from semantic_iot.tools import TOOLS, execute_tool

from pathlib import Path
root_path = Path(__file__).parent



class ClaudeAPIProcessor:    
    def __init__(self, 
                 api_key: str = "", 
                 model: str = "claude-3-7-sonnet-20250219",  
                 temperature: float = 1.0,
                 system_prompt: str = """
                    You are an expert in engineering who is specialized in developing knowledge graphps 
                    for building automation with IoT platforms. Be precise and concise.
                    You can use tools, only call them when needed.
                    Put the relevant output data in <output> tags.""",
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
        if api_key: self.api_key = api_key
        else:
            try:
                with open(f"{root_path}/ANTHROPIC_API_KEY", "r") as f:
                    self.api_key = f.read().strip()
            except FileNotFoundError:
                self.api_key = input(f"Couldn't find API key in {root_path}/ANTHROPIC_API_KEY\nEnter your Anthropic API key: ")
    
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt

        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        self.conversation_history = []
        self.metrics = {}
        self.tool_names = tool_names
        self.tools = TOOLS

    def query(self,
                    prompt: str = "",
                    step_name: str = 0,
                    max_retry: int = 5,
                    conversation_history = None,
                    temperature: float = None,
                    thinking: bool = False) -> Dict[str, Any]:
        """
        Send a query to Claude API

        Args:
            prompt: The prompt to send to Claude
            step_name: The name of the step
            max_retry: Maximum number of retries in case of a 429 error
            conversation_history: Optional conversation history to use for this query
            temperature: Optional temperature parameter to override the instance setting
            thinking: Enable thinking mode if the model supports it

        Returns:
            The JSON response from Claude
        """    
        
        
        print (f"✨ Claude generating... ({step_name})")
        
        # SETUP =========================================================================

        # Use instance data or default values
        temperature = temperature if temperature is not None \
            else self.temperature
        
        messages = conversation_history if conversation_history \
            else self.conversation_history.copy()

        if prompt: # Add user message to messages
            messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 20000,
            "system": self.system_prompt,
            "temperature": self.temperature, # "top_p": 1.0
            "tools": self.tools,
            "tool_choice": {"type": "auto"} # default
        }

        if thinking:
            data["thinking"] = {
                "type": "enabled",
                "budget_tokens": 16000
            }


        # QUERY ========================================================================

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
                    print(f"Received 429 error: Too many requests. Retrying in one minute... ({i + 1}/{max_retry})")
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
        
        # Process thinking content if present
        thinking_text = None
        response_text = None
        
        if result and "content" in result:
            for block in result["content"]:
                if "type" in block and block["type"] == "thinking" and "thinking" in block:
                    thinking_text = block["thinking"]
                elif "type" in block and block["type"] == "text" and "text" in block:
                    response_text = block["text"]
                elif "text" in block:
                    response_text = block["text"]

        # If no structured content types found, fallback to first content block
        if response_text is None and result and "content" in result and len(result["content"]) > 0:
            if "text" in result["content"][0]: # Handle case where response doesn't use the structured format
                response_text = result["content"][0]["text"]
        
        
        # Add assistant response to messages and update conversation history
        # print(f"Claude result: {result}")
        messages.append({"role": "assistant", "content": result["content"]})
        # messages.append({"role": "assistant", "content": response_text})
        self.conversation_history = messages
        

        # METRICS ======================================================== 

        # TODO implement time to first token metric
        # TODO implement time per token metric
        # TODO implement memory usage metric

        self.metrics[step_name] = {
            "prompt": prompt,
            "goal": None,
            "thinking": None,
            "response": response_text,
            "performance": {
                "time_seconds": None,
                "tokens": None,
                "memory": None
            },
            "evaluation": None,
        }

        # Goal
        match = re.search(r"<goal>(.*?)</goal>", prompt, re.DOTALL)
        goal = match.group(1).strip() if match else prompt

        match = re.search(r"<instructions>(.*?)</instructions>", prompt, re.DOTALL)
        instructions = match.group(1).strip() if match else prompt

        if goal: self.metrics[step_name]["goal"] = goal
        else:    self.metrics[step_name]["goal"] = prompt

        # Thinking
        if thinking_text: self.metrics[step_name]["thinking"] = thinking_text
        else:             self.metrics[step_name]["thinking"] = instructions

        # Time
        elapsed_time = end_time - start_time
        self.metrics[step_name]["performance"]["time_seconds"] = elapsed_time
        # print(f"⌛ Query time: {elapsed_time:.2f} seconds")

        # Tokens
        # self.metrics[step_name]["performance"]["tokens"] = result.get("usage", {})
        self.metrics[step_name]["performance"]["input_tokens"] = result.get("usage", {}).get("input_tokens", 0)
        self.metrics[step_name]["performance"]["output_tokens"] = result.get("usage", {}).get("output_tokens", 0)
        
        print(f"📐 Metrics: \n  {json.dumps(self.metrics[step_name], indent=2)}")


        # TOOL USE =========================================================

        if result.get("stop_reason") == "tool_use":
            tool_use = result.get("content")[-1] # TODO assuming only one tool is called at a time
            tool_name = tool_use.get("name")
            tool_input = tool_use.get("input")

            print(f"🛠️  Tool use... ({tool_name})")
            tool_result = execute_tool(tool_name, tool_input)
            print(f"Tool result: {tool_result}")

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.get("id"),
                            "content": str(tool_result)
                        }
                    ],
                },
            )
            self.conversation_history = messages

            # self.metrics[step_name]["tool_use"] = {
            #     "tool_name": tool_name,
            #     "tool_input": tool_input,
            #     "tool_result": tool_result
            # }

            self.query(step_name=f"{step_name}_follow_up", thinking=thinking)

        elif result.get("stop_reason") == "end_turn":
            model_reply = self.extract_tag(response_text, "output")
            print(f"↪️  Claude reply: {response_text}")
            return response_text

        else: raise Exception("Unknown stop reason")
        
    
    def regenerate (self, error_message) -> None:
        '''
        Correct generated content based on error messages.
        '''
        response = self.query(f"""
            The goal of this prompt is the same as the previous one. Now consider the error message.

            ERROR MESSAGE:
            {error_message}
        """)
        return response

    def save_results(self, output_file: str) -> None:
        """
        Save the pipeline results to a JSON file

        Args:
            output_file: Path to the output JSON file
        """
        with open(output_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

        print(f"\nResults saved to {output_file}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the metrics of the pipeline

        Returns:
            The metrics of the pipeline
        """
        print(f"📐 Metrics: {self.metrics}")
        return self.metrics

    def extract_tag(self, text, tag):
        pattern = fr'<{tag}>(.*?)</{tag}>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return None