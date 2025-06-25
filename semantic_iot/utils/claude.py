import time
from datetime import datetime
import requests
import json
import re
import anthropic
from typing import Dict, Any, List, Optional, Union
from memory_profiler import memory_usage
import yaml
from mermaid import Mermaid
import textwrap

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
        "max_tokens": 40000, #max:64000
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


class LLMAgent:    
    def __init__(self, 
                 api_key: str = "", 
                 model: str = "4sonnet",
                 temperature: float = 1.0,
                 system_prompt: str = prompts.system_default,
                 result_folder: str = "LLM_models/metrics",):
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

                with open(f"{root_path}/ANTHROPIC_API_KEY", "w") as f:
                    f.write(self.api_key)
                print(f"API key saved to {root_path}/ANTHROPIC_API_KEY")
    
        if model not in models:
            raise ValueError(f"Model {model} not found. Available models: {list(models.keys())}")
        self.model = models[model]
        self.model_name = model
        self.model_api = self.model["api"]
        self.thinking = self.model["thinking"]
        self.max_tokens = self.model["max_tokens"]
        # print (f"\nUsing Claude model: {self.model_api} (Thinking Possible: {self.thinking}, Max Tokens: {self.max_tokens})")

        self.temperature = temperature
        self.system_prompt = system_prompt if system_prompt else "default"

        self.result_folder = result_folder

        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "anthropic-beta": "interleaved-thinking-2025-05-14"

        }

        # self.client = anthropic.Client(self.api_key) # TODO replace with API instead of requests
        
        self.conversation_history = []
        self.metrics = {}
        self.yaml_text = {}

    def query(self,
                prompt: str = "",
                step_name: str = "default_step",
                max_retry: int = 5,
                max_tokens: int = None,
                conversation_history = None,
                temperature: float = None,
                thinking: bool = True,
                tools: str = "",
                follow_up: bool = False,
                stop_sequences: List[str] = []) -> Dict[str, Any]:
        """
        Send a query to Claude API

        Args:
            prompt: The prompt to send to Claude
            step_name: The name of the step
            max_retry: Maximum number of retries in case of a 429 error
            conversation_history: Optional conversation history to use for this query
            temperature: Optional temperature parameter to override the instance setting
            thinking: Enable thinking mode if the model supports it
            tools: Tools to make available to Claude (e.g. "context", "file_access", "validation", "rml_engine", "siot_tools")
            follow_up: Whether this is a follow-up query (to add cache breakpoints)

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
        
        print (f"\n✨ {str(self.model_api).capitalize()}{'-Thinking' if thinking else ''} generating... ({step_name})")

        
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
        
        if max_tokens:
            self.max_tokens = max_tokens
            print(f"🔧 Overriding max_tokens to {self.max_tokens} for this query")

        if prompt: # Add user message to messages
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
            "temperature": self.temperature,
            "stop_sequences": stop_sequences,
        }
        if follow_up: # Add Cache Breakpoint if multiple queries are made
            data["system"][0]["cache_control"] = {"type": "ephemeral"} 

        if thinking:
            data["thinking"] = {
                "type": "enabled",
                "budget_tokens": int(self.max_tokens*0.8) # how much? default: 16000
            }
        
        if tools:
            from semantic_iot.utils.tools import execute_tool, FILE_ACCESS, CONTEXT, VALIDATION, RML_ENGINE, SIOT_TOOLS
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
                print("⌚ API is temporarily overloaded, trying again in one minute...")
                time.sleep(60)  
                continue
            elif response.status_code == 502: # Bad Gateway
                print("⌚ Bad Gateway from API server, trying again in one minute...")
                time.sleep(60)
                continue
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

        self.metrics[step_name] = {
            "step_name": step_name,
            "prompt": prompt,
            "thinking": thinking_text if thinking_text else "No Thinking",
            "response": response_text,
            "model": self.model_api,
            "performance": {
                "time": {
                    "latency": round(elapsed_time, 2),
                    "tpot": round(elapsed_time / result.get("usage", {}).get("output_tokens", 1), 4),
                    "ttft": None
                },
                "tokens": result.get("usage", {})            
            },
            # "sub_steps": self._parse_steps(thinking_text, response_text)
        }
        self.save_json_metrics(step_name)



        self._add_newline(prompt, f"{self.result_folder}/prompt.md")
        if thinking_text:
            self._add_newline(thinking_text, f"{self.result_folder}/thinking.md")
        self._add_newline(response_text, f"{self.result_folder}/response.md")

        steps = self._parse_steps(thinking_text, response_text)
        if steps:
            self.save_yaml(steps, f"{self.result_folder}/steps.yaml")

        mermaid_flowchart = self.extract_code(self.extract_tag(response_text, "flowchart"))
        if mermaid_flowchart:
            Mermaid(graph=mermaid_flowchart).to_svg(f"{self.result_folder}/flowchart.svg")
        
        print(f"⬇️  Metrics saved to {self.result_folder}")



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
            self.save_json_metrics(tool_name)

            # FOLLOW UP
            if follow_up: 
                tool_result = self.query(
                    step_name=f"{step_name}", 
                    thinking=thinking, 
                    tools=tools,
                    follow_up=follow_up,
                    stop_sequences=stop_sequences
                )
                return tool_result
            else:
                print("Returning tool result...")
                return tool_result
            
        # STOP SEQUENCE =========================================
        if result.get("stop_reason") == "stop_sequence":
            print(f"⏸️ Stopped at sequence: {result.get('stop_sequence')}")
            output = self.extract_tag(response_text, "output")
            if output: response_text = output
            print(f"✨↪️  Model reply: {response_text}")
            return response_text

            # Parse Steps anyway, without <tags> and thinking_text
            # ...
    
        
        # END OF TERM & MAX TOKENS =========================================================
        elif result.get("stop_reason") == "end_turn":
            output = self.extract_tag(response_text, "output")
            if output: response_text = output
            print(f"✨↪️  Model reply: {response_text}")
            return response_text

        elif result.get("stop_reason") == "max_tokens":
            print("⚠️  Max tokens reached, response may be incomplete.")
            i = input("Continue generation? (y/n)")
            if i.strip().lower() == 'y':
                print("Continuing generation...")
                # Continue the query with the same prompt and conversation history
                return self.query(
                    prompt=prompt+response_text, # Append the response text to the prompt
                    step_name=step_name,
                    max_retry=max_retry,
                    temperature=temperature,
                    thinking=thinking,
                    tools=tools,
                    follow_up=follow_up,
                    stop_sequences=stop_sequences
                )
            else:
                print("Stopping generation.")
                print(f"✨↪️  Model reply: {response_text}")
                return self.extract_tag(response_text, "output") if self.extract_tag(response_text, "output") else response_text

        else: raise Exception("Unknown stop reason")
        
    
    def regenerate (self, error_message) -> None:
        '''
        Correct generated content based on error messages.
        '''
        response = self.query(f"""
            The goal of this prompt is the same as the previous one. Now consider the error message.

            ERROR MESSAGE:
            {error_message}
        """, step_name="regenerate_response")
        return response

    def save_json_metrics(self, step_name: str, output_file: str="LLM_models/metrics/metrics.json") -> None:
        """
        Save the pipeline results to a JSON file, appending or updating the dict.

        Args:
            output_file: Path to the output JSON file
        """
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

    def save_yaml(self, text: str, output_file: str) -> None:
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except FileNotFoundError:
            existing_content = ""
        
        content = existing_content + "\n\n\n" + text 

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
                # yaml.dump(text, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"⚠️  Error saving metrics to YAML: {e}")

    def _add_newline(self, string, path: str):
        # Retrieve existing content
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except FileNotFoundError:
            existing_content = ""

        # Add new content
        for line in string.split("\n"):
            existing_content += f"{line}\n"

        with open(path, "w", encoding="utf-8") as f:
            f.write(existing_content)

        return existing_content


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
            except json.JSONDecodeError as e:
                # print(f"⚠️  JSON parsing error in code block: {e}")
                # print(f"Content: {extracted_content[:200]}...")
                # Try to extract just valid JSON from the beginning
                try:
                    decoder = json.JSONDecoder()
                    obj, idx = decoder.raw_decode(extracted_content)
                    # print(f"✅ Extracted valid JSON object from position 0 to {idx}")
                    return obj
                except json.JSONDecodeError:
                    # print("ℹ️ Could not extract valid JSON, returning raw content")
                    return extracted_content
        else:
            # No code block found, check if the text itself is already a dict or valid JSON
            if isinstance(text, dict):
                return text
            elif isinstance(text, str):
                try:
                    return json.loads(text)
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON parsing error in raw text: {e}")
                    print(f"Content: {text[:200]}...")
                    # Try to extract just valid JSON from the beginning
                    try:
                        decoder = json.JSONDecoder()
                        obj, idx = decoder.raw_decode(text)
                        print(f"✅ Extracted valid JSON object from position 0 to {idx}")
                        return obj
                    except json.JSONDecodeError:
                        print("❌ Could not extract valid JSON, returning raw text")
                        return text
            else:
                return text

    def _parse_steps(self, thinking_text, response_text):
        """
        Safely parse steps from extracted text with proper error handling.
        
        Args:
            thinking_text: The thinking text from Claude's response
            response_text: The response text from Claude's response
            
        Returns:
            dict or None: Parsed steps as dict if valid JSON, otherwise None
        """
        # Try parsing steps from response first
        # print("🔍 Attempting to parse steps from response text...")
        try:
            steps_text = self.extract_tag(response_text, "steps")
            if steps_text:
                return self._extract_evaluations(steps_text)
        except Exception as e:
            print(f"⚠️  Error parsing thinking steps: {e}")        
        
        # Parse steps from thinking text
        # print("🔍 Attempting to parse steps from thinking text...")
        try:
            steps_text = self.extract_tag(thinking_text, "steps")
            if steps_text:
                return self._extract_evaluations(thinking_text)
        except Exception as e:
            print(f"⚠️  Error parsing thinking steps: {e}")
        return None
    
    def _extract_evaluations(self, text: str):
        """
        Extracts evaluation sections from text that start with 'EVALUATION:' 
        and continue until an empty line is encountered.
        """
        evaluations = ""
        lines = text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("EVALUATION:"):
                evaluation_lines = [line]
                i += 1
                
                while i < len(lines):
                    current_line = lines[i]

                    # If line contains " - " (dash with spaces), keep only the part before it
                    if " - " in current_line.strip():
                        current_line = current_line.split(" - ")[0]
                    
                    if current_line.strip() == "":
                        break
                    evaluation_lines.append(current_line)
                    i += 1
                
                evaluations += '\n'.join(evaluation_lines) + "\n\n"
            i += 1

        print(f"🔍 Found {evaluations.count('EVALUATION:')} evaluations in text")
        print(evaluations)

        return evaluations
    
    def _parse_thinking_steps(self, thinking_text):
        """
        Parse steps from thinking text format.
        
        Args:
            thinking_text: The thinking text containing step information
            
        Returns:
            dict: Parsed steps with step numbers as keys
        """
        if not thinking_text:
            return None
            
        steps = {}
        
        # Split the text by double newlines to get step blocks
        # Then find blocks that start with "Step"
        blocks = thinking_text.split('\n\n')
        
        print(f"🔍 Found {len(blocks)} blocks in thinking text")
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
                
            # Check if this block starts with "Step"
            if re.match(r'^\s*Step\s+\d+:', block, re.IGNORECASE):
                # Extract step number and content
                step_match = re.match(r'^\s*Step\s+(\d+):\s*(.*)', block, re.DOTALL | re.IGNORECASE)
                if step_match:
                    step_number = step_match.group(1)
                    step_content = step_match.group(2).strip()
                    
                    # Split into lines to get title and attributes
                    lines = step_content.split('\n')
                    step_title = lines[0].strip()
                    
                    # Parse the step details (bloom, dim, quantity, human_effort)
                    step_data = {
                        "title": step_title,
                        "bloom": None,
                        "dim": None,
                        "quantity": None,
                        "human_effort": None
                    }
                    
                    # print(f"Step {step_number} block: {repr(block)}")
                    
                    # Look for attributes in the entire block
                    for line in lines:
                        line = line.strip()
                        
                        # Extract bloom value
                        bloom_match = re.search(r'bloom:\s*([^\n,]+)', line, re.IGNORECASE)
                        if bloom_match:
                            step_data["bloom"] = bloom_match.group(1).strip()
                        
                        # Extract dim value
                        dim_match = re.search(r'dim:\s*([^\n,]+)', line, re.IGNORECASE)
                        if dim_match:
                            step_data["dim"] = dim_match.group(1).strip()
                        
                        # Extract quantity value
                        quantity_match = re.search(r'quantity:\s*(\d+)', line, re.IGNORECASE)
                        if quantity_match:
                            step_data["quantity"] = int(quantity_match.group(1))
                        
                        # Extract human_effort value
                        effort_match = re.search(r'human_effort:\s*(\d+)', line, re.IGNORECASE)
                        if effort_match:
                            step_data["human_effort"] = int(effort_match.group(1))
                    
                    print(f"Parsed step {step_number}: {step_data}")

                    # Only include steps that have all required fields
                    if all(step_data[key] is not None for key in ["bloom", "dim", "quantity", "human_effort"]):
                        steps[f"step_{step_number}"] = step_data
                    else:
                        print(f"⚠️ Step {step_number} missing required fields: {[k for k, v in step_data.items() if v is None]}")
        
        return steps if steps else None
    


if __name__ == "__main__":

    thinking_text = """
    "response": "<flowchart>\n```mermaid\nflowchart TD\n    A[Start] --> B[Read sequence terms]\n    B --> C[Calculate ratio 2/1]\n    C --> D[Calculate ratio 4/2]\n    D --> E[Calculate ratio 8/4]\n    E --> F[Identify common pattern]\n    F --> G[Generate term 5]\n    G --> H[Generate term 6]\n    H --> I[Generate term 7]\n    I --> J[End]\n```\n</flowchart>\n\n<estimation>\n9 steps total (8 process nodes + completion)\n</estimation>\n\n<steps>\n\nSTEP 1: read 4 sequence terms\n- flowchart_node: Read sequence terms\n- context: Given sequence \"1, 2, 4, 8, ...\"\n\nEXECUTING:\nReading the provided sequence terms:\n- Term 1: 1\n- Term 2: 2  \n- Term 3: 4\n- Term 4: 8\n\nVALIDATION:\n- single_bloom_check: Knowledge - only retrieving given information\n- subdivision_check: Cannot be subdivided - single reading action\n- step_validation_checklist: Single action (read), single Bloom level (Knowledge), single output (4 terms), atomic operation\n\nEVALUATION:\n- bloom: Knowledge - recall given sequence terms\n- dim: Factual Knowledge\n- quantity: 4\n- human_effort: 5 - Simple reading of provided numbers\n\nNEXT: STEP 2: Calculate ratio 2/1\n- next_flowchart_node: Calculate ratio 2/1\n\nSTEP 2: calculate 1 ratio between consecutive terms\n- flowchart_node: Calculate ratio 2/1\n- context: Term 1 = 1, Term 2 = 2\n\nEXECUTING:\nCalculating the ratio between the second and first terms:\nRatio = Term 2 ÷ Term 1 = 2 ÷ 1 = 2\n\nVALIDATION:\n- single_bloom_check: Application - applying division operation\n- subdivision_check: Cannot be subdivided - single calculation\n- step_validation_checklist: Single action (calculate), single Bloom level (Application), single output (ratio = 2), atomic operation\n\nEVALUATION:\n- bloom: Application - apply division to find ratio\n- dim: Procedural Knowledge\n- quantity: 1\n- human_effort: 10 - Basic arithmetic calculation\n\nNEXT: STEP 3: Calculate ratio 4/2\n- next_flowchart_node: Calculate ratio 4/2\n\nSTEP 3: calculate 1 ratio between consecutive terms\n- flowchart_node: Calculate ratio 4/2\n- context: Term 2 = 2, Term 3 = 4\n\nEXECUTING:\nCalculating the ratio between the third and second terms:\nRatio = Term 3 ÷ Term 2 = 4 ÷ 2 = 2\n\nVALIDATION:\n- single_bloom_check: Application - applying division operation\n- subdivision_check: Cannot be subdivided - single calculation\n- step_validation_checklist: Single action (calculate), single Bloom level (Application), single output (ratio = 2), atomic operation\n\nEVALUATION:\n- bloom: Application - apply division to find ratio\n- dim: Procedural Knowledge\n- quantity: 1\n- human_effort: 10 - Basic arithmetic calculation\n\nNEXT: STEP 4: Calculate ratio 8/4\n- next_flowchart_node: Calculate ratio 8/4\n\nSTEP 4: calculate 1 ratio between consecutive terms\n- flowchart_node: Calculate ratio 8/4\n- context: Term 3 = 4, Term 4 = 8\n\nEXECUTING:\nCalculating the ratio between the fourth and third terms:\nRatio = Term 4 ÷ Term 3 = 8 ÷ 4 = 2\n\nVALIDATION:\n- single_bloom_check: Application - applying division operation\n- subdivision_check: Cannot be subdivided - single calculation\n- step_validation_checklist: Single action (calculate), single Bloom level (Application), single output (ratio = 2), atomic operation\n\nEVALUATION:\n- bloom: Application - apply division to find ratio\n- dim: Procedural Knowledge\n- quantity: 1\n- human_effort: 10 - Basic arithmetic calculation\n\nNEXT: STEP 5: Identify common pattern\n- next_flowchart_node: Identify common pattern\n\nSTEP 5: identify 1 common pattern from ratios\n- flowchart_node: Identify common pattern\n- context: Calculated ratios are 2, 2, 2\n\nEXECUTING:\nAnalyzing the calculated ratios:\n- Ratio 1: 2\n- Ratio 2: 2  \n- Ratio 3: 2\n\nAll ratios are equal to 2, indicating this is a geometric sequence with common ratio r = 2.\nPattern identified: Each term is double the previous term.\n\nVALIDATION:\n- single_bloom_check: Analysis - examining ratios to identify pattern\n- subdivision_check: Cannot be subdivided - single pattern recognition\n- step_validation_checklist: Single action (identify), single Bloom level (Analysis), single output (pattern = geometric sequence with r=2), atomic operation\n\nEVALUATION:\n- bloom: Analysis - analyze ratios to identify pattern\n- dim: Conceptual Knowledge\n- quantity: 1\n- human_effort: 25 - Requires pattern recognition and understanding of geometric sequences\n\nNEXT: STEP 6: Generate term 5\n- next_flowchart_node: Generate term 5\n\nSTEP 6: generate 1 next sequence term\n- flowchart_node: Generate term 5\n- context: Term 4 = 8, common ratio = 2\n\nEXECUTING:\nApplying the identified pattern to generate the 5th term:\nTerm 5 = Term 4 × common ratio = 8 × 2 = 16\n\nVALIDATION:\n- single_bloom_check: Application - applying identified pattern\n- subdivision_check: Cannot be subdivided - single term generation\n- step_validation_checklist: Single action (generate), single Bloom level (Application), single output (term 5 = 16), atomic operation\n\nEVALUATION:\n- bloom: Application - apply pattern to generate term\n- dim: Procedural Knowledge\n- quantity: 1\n- human_effort: 15 - Straightforward application of identified pattern\n\nNEXT: STEP 7: Generate term 6\n- next_flowchart_node: Generate term 6\n\nSTEP 7: generate 1 next sequence term\n- flowchart_node: Generate term 6\n- context: Term 5 = 16, common ratio = 2\n\nEXECUTING:\nApplying the identified pattern to generate the 6th term:\nTerm 6 = Term 5 × common ratio = 16 × 2 = 32\n\nVALIDATION:\n- single_bloom_check: Application - applying identified pattern\n- subdivision_check: Cannot be subdivided - single term generation\n- step_validation_checklist: Single action (generate), single Bloom level (Application), single output (term 6 = 32), atomic operation\n\nEVALUATION:\n- bloom: Application - apply pattern to generate term\n- dim: Procedural Knowledge\n- quantity: 1\n- human_effort: 15 - Straightforward application of identified pattern\n\nNEXT: STEP 8: Generate term 7\n- next_flowchart_node: Generate term 7\n\nSTEP 8: generate 1 next sequence term\n- flowchart_node: Generate term 7\n- context: Term 6 = 32, common ratio = 2\n\nEXECUTING:\nApplying the identified pattern to generate the 7th term:\nTerm 7 = Term 6 × common ratio = 32 × 2 = 64\n\nVALIDATION:\n- single_bloom_check: Application - applying identified pattern\n- subdivision_check: Cannot be subdivided - single term generation\n- step_validation_checklist: Single action (generate), single Bloom level (Application), single output (term 7 = 64), atomic operation\n\nEVALUATION:\n- bloom: Application - apply pattern to generate term\n- dim: Procedural Knowledge\n- quantity: 1\n- human_effort: 15 - Straightforward application of identified pattern\n\nNEXT: Task completion\n- next_flowchart_node: End\n\n</steps>\n\n<output>\nThe completed sequence is: 1, 2, 4, 8, 16, 32, 64, ...\n\nThis is a geometric sequence where each term is obtained by multiplying the previous term by 2 (common ratio = 2).\n</output>\n\n<verification>\nEVALUATION TOTAL:\n- Total Steps: 8\n- Flowchart Compliance: yes - all steps correspond to flowchart process nodes\n- Bloom Consistency: yes - each step uses only one Bloom level (Knowledge, Application, or Analysis)\n- Granularity Check: yes - similar operations (ratio calculations, term generations) have consistent granularity\n</verification>",
    """

    # Example usage
    claude = LLMAgent()

    # Print the parsed steps
    # result = claude._parse_thinking_steps(thinking_text)
    result = claude._parse_steps(thinking_text, thinking_text)
    print("\n\n")
    print(result)
    # print(json.dumps(result, indent=2))