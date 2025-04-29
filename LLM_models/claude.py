import time
from datetime import datetime
import requests
import json
from typing import Dict, Any

from pathlib import Path
root_path = Path(__file__).parent


# py -m pip install .

class ClaudeAPIProcessor:
    def __init__(self, api_key: str = "", model: str = "claude-3-5-sonnet-20241022", use_api: bool = True, temperature: float = 1.0):
        """
        Initialize the Claude API processor

        Args:
            api_key: Your Anthropic API key
            model: Claude model to use
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

        # Dictionary to store step responses
        self.step_results = {}

    def query(self,
                     prompt: str,
                     step_name: str = 0,
                     max_retry: int = 5,
                     conversation_history=None,
                     temperature: float = None) -> Dict[str, Any]:
        """
        Send a query to Claude API

        Args:
            prompt: The prompt to send to Claude
            step_name: The name of the step
            max_retry: Maximum number of retries in case of a 429 error
            conversation_history: Optional conversation history to use for this query

        Returns:
            The JSON response from Claude
        """

        print ("✨ Generating with Claude...")

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
            "max_tokens": 4000,
            "temperature": self.temperature # "top_p": 1.0
            
        }

        result = None
        for i in range(max_retry):
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(data)
            )
            if response.status_code == 200: # Request successful
                result = response.json()
                break
            elif response.status_code == 429: # Too many requests
                if i < max_retry - 1:
                    print(f"Received 429 error. Retrying... ({i + 1}/{max_retry})")
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
                                f"status code {response.status_code}")
        # Add assistant response to the provided messages list
        messages.append({
            "role": "assistant",
            "content": result["content"][0]["text"]
        })

        # Save the step results
        self.step_results[step_name] = {
            "prompt": prompt,
            "response": result["content"][0]["text"]
        }

        # Update instance conversation history if using it
        if not conversation_history:
            self.conversation_history = messages

        return result["content"][0]["text"]
    
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

