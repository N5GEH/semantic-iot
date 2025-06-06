import time
from datetime import datetime
import requests
import json
import re
import anthropic
from typing import Dict, Any, List, Optional, Union
from memory_profiler import memory_usage

from semantic_iot.utils.prompts import prompts

from pathlib import Path
root_path = Path(__file__).parent

# Price in $ per million tokens (Base Input) (https://docs.anthropic.com/en/docs/about-claude/models/overview)
models = {
    "4opus": {
        "api": "claude-opus-4-20250514",
        "thinking": True,
        "max_tokens": 20000, #max:32000
        "price": 15.0,  
    },
    "4sonnet": {
        "api": "claude-sonnet-4-20250514",
        "thinking": True, # Summarized Thinking
        "max_tokens": 20000, #max:64000
        "price": 3.0, 
    },
    "3.7sonnet": {
        "api": "claude-3-7-sonnet-20250219",
        "thinking": True, # Full Thinking
        "max_tokens": 20000, #max:64000
        "price": 3.0,  
    },
    "3.5haiku": {
        "api": "claude-3-5-haiku-20241022",
        "thinking": False,
        "max_tokens": 8192, #max:8192
        "price": 0.8,  
    },
    "3haiku": {
        "api": "claude-3-haiku-20240307",
        "thinking": False,
        "max_tokens": 4096, #max:4096
        "price": 0.25,  
    },
}


class ClaudeAPIProcessor:    
    def __init__(self, 
                 api_key: str = "", 
                 model: str = "4sonnet",
                 temperature: float = 1.0, # TUNE
                 system_prompt: str = prompts.system_default):
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
    
        if model not in models:
            raise ValueError(f"Model {model} not found. Available models: {list(models.keys())}")
        self.model = models[model]
        self.model_api = self.model["api"]
        self.thinking = self.model["thinking"]
        self.max_tokens = self.model["max_tokens"]
        print (f"Using Claude model: {self.model_api} (Thinking: {self.thinking}, Max Tokens: {self.max_tokens})")

        self.temperature = temperature
        self.system_prompt = system_prompt if system_prompt else "default"

        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "anthropic-beta": "interleaved-thinking-2025-05-14"

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
                    thinking: bool = False,
                    tools: str = "",
                    follow_up: bool = False) -> Dict[str, Any]: # TODO add tool selection
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

        # Check if thinking is enabled for the model
        if not self.thinking and thinking:
            print("⚠️  Thinking mode is not supported for this model, continuing without thinking.")
            thinking = False            

        # Use instance data or default values
        temperature = temperature if temperature is not None \
            else self.temperature
        if thinking: temperature = 1.0
        
        messages = conversation_history if conversation_history \
            else self.conversation_history.copy()

        if prompt: # Add user message to messages
            prompt += prompts.cot_extraction_full
            messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model_api,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": self.system_prompt,
                }
            ],
            "temperature": self.temperature # "top_p": 1.0
        }
        if follow_up: # Add Cache Breakpoint if multiple queries are made
            data["system"][0]["cache_control"] = {"type": "ephemeral"} 

        if thinking:
            data["thinking"] = {
                "type": "enabled",
                "budget_tokens": int(self.max_tokens*0.8) # TODO how much? default: 16000
            }
        
        if tools:
            from semantic_iot.tools import execute_tool, FILE_ACCESS, CONTEXT, VALIDATION, RML_ENGINE, SIOT_TOOLS
            selected_tools = []
            if "context"     in tools: selected_tools.extend(CONTEXT)
            if "file_access" in tools: selected_tools.extend(FILE_ACCESS)
            if "validation"  in tools: selected_tools.extend(VALIDATION)
            if "rml_engine"  in tools: selected_tools.extend(RML_ENGINE)
            if "siot_tools"  in tools: selected_tools.extend(SIOT_TOOLS)

            if selected_tools:
                if follow_up: # Add Cache Breakpoint if multiple queries are made
                    tools_with_cache = selected_tools.copy()
                    # Only if the last tool doesn't already have it
                    if tools_with_cache and not tools_with_cache[-1].get("cache_control"):
                        tools_with_cache[-1]["cache_control"] = {"type": "ephemeral"}
                    data["tools"] = tools_with_cache
                data["tool_choice"] = {"type": "auto"} # default
            else: print("ℹ️  Tool selection invalid, continuing without tools")  


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
            },
            "sub_steps": json.loads(self.extract_tag(response_text, "steps")) if self.extract_tag(response_text, "steps") else None
            # "evaluation": None, # TODO add absolute evaluation based on ... ??
        }      
        self.save_metrics(step_name)


        # TOOL USE =========================================================

        if tools and result.get("stop_reason") == "tool_use":
            tool_use = result.get("content")[-1] # TODO assuming only one tool is called at a time
            tool_name = tool_use.get("name")
            tool_input = tool_use.get("input")

            print(f"\n🛠️  Tool use... ({tool_name})")
            try:
                tool_result = execute_tool(tool_name, tool_input)
            except Exception as e:
                error_message = f"⚠️  Error executing tool '{tool_name}': {e}"
                print(error_message)

                
                tool_result = {
                    "error": True,
                    "message": error_message,
                    "details": str(e)
                }
                
                # if input("Do you want to regenerate the response? (y/n): ").strip().lower() == 'n':
                #     raise e
                print("Continuing with error result...")  # Continue with the error result
                
                # Don't raise the exception, just continue with the error result

            print(f"🛠️ ↪️  Tool result: \n{json.dumps(tool_result, indent=2)}")

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
            if tool_name == "load_from_file": # add breakpoint behind file loading
                if not tool_result.get("error"):
                    if messages and isinstance(messages[-1], dict) and isinstance(messages[-1]["content"], list):
                        if len(messages[-1]["content"]) > 0:

                            cache_control_count = 0
                            cache_control_locations = []
                            for msg_idx, msg in enumerate(messages):
                                if isinstance(msg, dict) and "content" in msg:
                                    content = msg["content"]
                                    if isinstance(content, list):
                                        for block_idx, block in enumerate(content):
                                            if isinstance(block, dict) and "cache_control" in block:
                                                cache_control_count += 1
                                                cache_control_locations.append((msg_idx, block_idx))
                                    elif isinstance(content, dict) and "cache_control" in content:
                                        cache_control_count += 1
                                        cache_control_locations.append((msg_idx, None))
                            print(f"ℹ️  Number of cache_control points in messages: {cache_control_count}")

                            # If there are exactly 2 cache_control points, remove the last one
                            if cache_control_count == 2 and cache_control_locations:
                                last_msg_idx, last_block_idx = cache_control_locations[-1]
                                if last_block_idx is not None:
                                    # Remove cache_control from the last block in the list
                                    messages[last_msg_idx]["content"][last_block_idx].pop("cache_control", None)
                                else:
                                    # Remove cache_control from the dict content
                                    messages[last_msg_idx]["content"].pop("cache_control", None)
                                print("🧹 Removed last cache_control breakpoint because there were 2.")

                            messages[-1]["content"][0]["cache_control"] = {"type": "ephemeral"}
                            print(f"📂 Loaded file, added cache breakpoint")
                            # print(f"📂 Messages: \n{json.dumps(messages, indent=2)}")
            


            self.conversation_history = messages

            # METRICS
            self.metrics[tool_name] = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_result": tool_result
            }
            self.save_metrics(tool_name)

            # FOLLOW UP
            if follow_up: 
                tool_result = self.query(
                    step_name=f"{step_name}", 
                    thinking=thinking, 
                    tools=tools,
                    follow_up=follow_up)
                return tool_result
            else:
                print("Returning tool result...")
                return tool_result

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
            with open(output_file, 'r', encoding='utf-8') as f:
                all_metrics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_metrics = {}

        # Update or add the current step's metrics
        if step_name in all_metrics:
            new_step_name = f"{step_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else: 
            new_step_name = step_name

        all_metrics[new_step_name] = self.metrics[step_name]

        # Write back the updated metrics with proper formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_metrics, f, indent=4, ensure_ascii=False)

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
        if text is None:
            return None
        pattern = fr'<{tag}>(.*?)</{tag}>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return None
        
    def extract_code(self, text):
        """
        Extract code blocks from text enclosed in triple backticks with optional language specification.
        
        Args:
            text: The text containing code blocks
            
        Returns:
            dict or str: The extracted code content parsed as JSON if valid, 
                        otherwise raw string content, or original text if no code block is found
        """
        if text is None:
            return None
        
        pattern = r'```(?:\w+)?\s*(.*?)\s*```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
            # Try to parse as JSON first
            try:
                return json.loads(extracted_content)
            except json.JSONDecodeError:
                return extracted_content
        else:
            # No code block found, check if the text itself is already a dict or valid JSON
            if isinstance(text, dict):
                return text
            elif isinstance(text, str):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
            else:
                return text