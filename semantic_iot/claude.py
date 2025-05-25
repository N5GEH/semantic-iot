import time
from datetime import datetime
import requests
import json
import re
import anthropic
from typing import Dict, Any, List, Optional, Union
from memory_profiler import memory_usage

from pathlib import Path
root_path = Path(__file__).parent



class ClaudeAPIProcessor:    
    def __init__(self, 
                 api_key: str = "", 
                 model: str = "claude-3-7-sonnet-20250219",  
                 temperature: float = 1.0,
                 system_prompt: str = """ 
                    You are an expert in engineering who is specialized in developing knowledge graphps 
                    for building automation with IoT platforms. 
                    Be precise and concise.
                    You can use tools, only call them when needed. 
                    When you call a tool, you will receive its output in the next interaction.
                    Put the relevant output data in <output> tags.
                    The parent of 'LLM_models' folder is the project root."""): # TODO include <background> from prompts.py
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

        # self.client = anthropic.Client(self.api_key) # TODO 
        
        self.conversation_history = []
        self.metrics = {}

    def query(self,
                    prompt: str = "",
                    step_name: str = "default_step",
                    max_retry: int = 5,
                    conversation_history = None,
                    temperature: float = None,
                    thinking: bool = True,
                    tool_use: bool = True) -> Dict[str, Any]: # TODO add tool selection
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

        try: # increase step name number
            try:
                step_name, number = step_name.split("(")
                number = number.split(")")
                step_name = step_name + f"({int(number[0]) + 1})"
            except Exception as e:
                step_name = f"{step_name}_(0)"
        except Exception as e:
            raise Exception(f"Error parsing step name '{step_name}': {e}")
        
        print (f"\n✨ Claude generating... ({step_name})")
        
        # SETUP =========================================================================

        # Use instance data or default values
        temperature = temperature if temperature is not None \
            else self.temperature
        if thinking: temperature = 1.0
        
        messages = conversation_history if conversation_history \
            else self.conversation_history.copy()

        if prompt: # Add user message to messages
            messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 20000,
            "system": self.system_prompt,
            "temperature": self.temperature # "top_p": 1.0
        }

        if thinking:
            data["thinking"] = {
                "type": "enabled",
                "budget_tokens": 16000
            }
        
        if tool_use:
            from semantic_iot.tools import TOOLS, execute_tool, VAL_TOOLS
            self.tools = TOOLS + VAL_TOOLS

            data["tools"] = self.tools
            data["tool_choice"] = {"type": "auto"} # default


        # QUERY ========================================================================

        result = None
        for i in range(max_retry):
        # try: TODO return the error and regenerate
            start_time = time.time()
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(data)
            )
            end_time = time.time()
            elapsed_time = end_time - start_time

            if response.status_code == 200: # Request successful
                result = response.json()
                break
            elif response.status_code == 429: # Too many requests
                if i < max_retry - 1:
                    print(f"⌚ Received 429 error: Too many requests. Retrying in one minute... ({i + 1}/{max_retry})")
                    time.sleep(61)
                    continue
                else:
                    print(f"Error: {response.status_code}")
                    print(response.text)
                    raise Exception("Max retries reached. "
                                    "API request failed with status code 429")
            elif response.status_code == 529: # The service is overloaded
                print("⌚ API is temporarily overloaded, try again later")
                time.sleep(60)  # Wait for a minute before retrying
                continue
                # response = {"content": [{"type": "tool_use", "id": datetime.now().strftime('%Y%m%d_%H%M%S'), "name": "wait_for_sec", "input": {"seconds": 60}}], "stop_reason": "tool_use"}
            elif response.status_code == 502: # Bad Gateway 
                print("⌚ Bad Gateway from API server, try again later")
                time.sleep(60)  # Wait for a minute before retrying
                continue
                # response = {"content": [{"type": "tool_use", "id": datetime.now().strftime('%Y%m%d_%H%M%S'), "name": "wait_for_sec", "input": {"seconds": 60}}], "stop_reason": "tool_use"}
            else:
                print(f"Error: {response.status_code}")
                print(response.text)

                raise Exception(f"API request failed with "
                                f"status code {response.status_code}")        # Use streaming for tool calls if we have tools available
        
        # PROCESSING =========================================================

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

        # TODO implement time to first token metric -> antropic stream
        # TODO add claude instance 

        self.metrics[step_name] = {
            "step_name": step_name,
            "prompt": prompt,
            "thinking": thinking_text if thinking_text else "No Thinking",
            "response": response_text,
            "performance": {
                "time": {
                    "latency": round(elapsed_time, 2),
                    "tpot": round(elapsed_time / result.get("usage", {}).get("output_tokens", 1), 4),
                    "ttft": None
                },
                "tokens": result.get("usage", {})
            }
            # "evaluation": None, # TODO add absolute evaluation based on ... ??
        }      
        self.save_metrics(step_name)


        # TOOL USE =========================================================

        if tool_use and result.get("stop_reason") == "tool_use":
            tool_use = result.get("content")[-1] # TODO assuming only one tool is called at a time
            tool_name = tool_use.get("name")
            tool_input = tool_use.get("input")

            print(f"\n🛠️  Tool use... ({tool_name})")
            try:
                tool_result = execute_tool(tool_name, tool_input)
            except Exception as e:
                error_message = f"Error executing tool '{tool_name}': {e}"
                print(error_message)

                # if input("Do you want to regenerate the response? (y/n): ").strip().lower() == 'n':
                #     raise e
                
                tool_result = {
                    "error": True,
                    "message": error_message,
                    "details": str(e)
                }
                
                # Don't raise the exception, just continue with the error result

            print(f"🛠️↪️ Tool result: \n{json.dumps(tool_result, indent=2)}")

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

            # METRICS
            self.metrics[tool_name] = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_result": tool_result
            }
            self.save_metrics(tool_name)

            # FOLLOW UP
            self.query(step_name=f"{step_name}", thinking=thinking)

        elif result.get("stop_reason") == "end_turn":
            model_reply = self.extract_tag(response_text, "output")            
            if model_reply: response_text = model_reply
            print(f"✨↪️  Model reply: {response_text}")
            return response_text

        else: raise Exception("Unknown stop reason")
        
    
    def regenerate (self, error_message) -> None: # TODO replace throug try: in query
        '''
        Correct generated content based on error messages.
        '''
        response = self.query(f"""
            The goal of this prompt is the same as the previous one. Now consider the error message.

            ERROR MESSAGE:
            {error_message}
        """, step_name="regenerate_response")
        return response

    def save_metrics(self, step_name: str, output_file: str="LLM_models/metrics/metrics.json") -> None:
        """
        Save the pipeline results to a JSON file, appending or updating the dict.

        Args:
            output_file: Path to the output JSON file
        """
        # TODO copy metrics to a new file

        # Try to load existing metrics
        try:
            with open(output_file, 'r') as f:
                all_metrics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_metrics = {}

        # Update or add the current step's metrics
        if step_name in all_metrics:
            new_step_name = f"{step_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else: 
            new_step_name = step_name

        all_metrics[new_step_name] = self.metrics[step_name]

        # Write back the updated metrics
        with open(output_file, 'w') as f:
            json.dump(all_metrics, f, indent=4)

        # print(f"⬇️ 📐 Metrics saved to {output_file}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the metrics of the pipeline

        Returns:
            The metrics of the pipeline
        """
        print(f"📐 Metrics: \n{self.metrics}")
        return self.metrics

    def extract_tag(self, text, tag):
        pattern = fr'<{tag}>(.*?)</{tag}>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return None