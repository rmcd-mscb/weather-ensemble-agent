# src/weather_agent/agent.py
"""Weather Ensemble Agent - main agent loop.

This module implements an AI agent that uses Claude with tool calling (function calling)
to help users analyze weather forecasts. The agent follows an agentic loop pattern:
1. Receive user input
2. Send to Claude with available tools
3. Execute any tools Claude requests
4. Return results to Claude
5. Repeat until Claude provides a final answer

This pattern allows the AI to autonomously decide when and how to use tools to
accomplish the user's request.
"""

import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from weather_agent.tools.geocoding import geocode_location

# Load environment variables from .env file into os.environ
# This allows us to access secrets like ANTHROPIC_API_KEY using os.getenv()
load_dotenv()


class WeatherEnsembleAgent:
    """An AI agent for weather analysis using Claude and tool calling.

    This agent demonstrates the agentic loop pattern where an AI model can:
    - Reason about which tools to use
    - Call tools autonomously
    - Process tool results
    - Provide helpful responses based on tool outputs

    Attributes:
        client: Anthropic API client for making requests to Claude
        conversation_history: List of messages (currently unused, for future expansion)
        tools: List of tool definitions that Claude can call
    """

    def __init__(self):
        """Initialize the Weather Ensemble Agent.

        Sets up the Anthropic client with the API key from environment variables,
        initializes conversation history tracking, and defines available tools.

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not set in environment variables
        """
        # Initialize the Anthropic client with API key from .env file
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Track conversation history (for future use in multi-turn conversations)
        self.conversation_history = []

        # Define the tools available to the agent
        self.tools = self._define_tools()

    def _define_tools(self):
        """Define the tools available to the agent.

        Tools are defined using Anthropic's tool calling format, which follows
        JSON Schema for parameter validation. Each tool needs:
        - name: The function name that will be called
        - description: Instructions to Claude about when and how to use the tool
        - input_schema: JSON Schema defining the expected parameters

        The agent uses these definitions to:
        1. Tell Claude what tools are available
        2. Validate Claude's tool call requests
        3. Map tool names to actual Python functions

        Returns:
            list: List of tool definition dictionaries compatible with Anthropic's API
        """
        return [
            {
                "name": "geocode_location",
                "description": (
                    "Convert a location name or address to latitude/longitude "
                    "coordinates. Use this when you need coordinates for a location."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location string like 'Denver, CO' or 'New York City'",
                        }
                    },
                    "required": ["location"],
                },
            }
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict):
        """Execute a tool by name with the provided inputs.

        This method acts as a dispatcher, routing tool calls from Claude to the
        actual Python functions that implement the tools. It uses the tool name
        to determine which function to call and unpacks the input dictionary
        as keyword arguments.

        Args:
            tool_name: The name of the tool to execute (e.g., "geocode_location")
            tool_input: Dictionary of parameters to pass to the tool function
                       Keys must match the function's parameter names

        Returns:
            dict: The result from the tool execution (structure varies by tool)

        Raises:
            ValueError: If the tool_name doesn't match any known tools

        Example:
            >>> agent._execute_tool("geocode_location", {"location": "Denver, CO"})
            {'latitude': 39.7392, 'longitude': -104.9903, 'display_name': '...'}
        """
        if tool_name == "geocode_location":
            # Unpack the input dict as keyword arguments using **
            return geocode_location(**tool_input)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def run(self, user_message: str, max_iterations: int = 10):
        """Run the agentic loop to process a user message.

        This is the main execution method that implements the agentic loop:
        1. Send user message + tools to Claude
        2. Claude responds with either:
           a) A final text answer (stop_reason="end_turn")
           b) Tool calls to execute (stop_reason="tool_use")
        3. If tool calls: execute them and send results back to Claude
        4. Repeat until Claude provides a final answer or max iterations reached

        The loop allows Claude to:
        - Chain multiple tool calls together
        - Make decisions based on tool results
        - Gather all needed information before responding

        Args:
            user_message: The user's request or question
            max_iterations: Maximum number of loops to prevent infinite execution.
                          Each iteration is one request to Claude. Default is 10.

        Returns:
            str: The final response from Claude, or "Max iterations reached" if
                 the loop doesn't complete within max_iterations

        Example:
            >>> agent = WeatherEnsembleAgent()
            >>> response = agent.run("What are the coordinates for Denver?")
            >>> print(response)
            The coordinates for Denver, Colorado are approximately 39.74°N, 104.99°W.
        """
        # Print a visual separator and the user's message
        print(f"\n{'=' * 60}")
        print(f"USER: {user_message}")
        print(f"{'=' * 60}\n")

        # System prompt defines the agent's role and behavior
        # This guides Claude on how to use tools and format responses
        system_prompt = """You are a weather analysis agent. Your goal is to help users
understand weather forecasts by analyzing data from multiple weather models.

For now, you have access to geocoding. When given a location, convert it to coordinates.
Be concise and helpful."""

        # Initialize the conversation with the user's message
        # Messages alternate between "user" and "assistant" roles
        messages = [{"role": "user", "content": user_message}]

        # Agentic loop: continue until we get a final answer or hit max iterations
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"--- Iteration {iteration} ---")

            # Send request to Claude with:
            # - model: Which Claude model to use
            # - max_tokens: Maximum length of response
            # - system: Instructions for Claude's behavior
            # - messages: Conversation history (user messages + assistant responses + tool results)
            # - tools: Available tools Claude can choose to call
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=system_prompt,
                messages=messages,
                tools=self.tools,
            )

            # stop_reason tells us why Claude stopped generating:
            # - "end_turn": Claude finished and provided a final answer
            # - "tool_use": Claude wants to call one or more tools
            # - "max_tokens": Response was cut off (rare with good max_tokens setting)
            print(f"Stop reason: {response.stop_reason}")

            # Case 1: Claude provided a final answer (no more tool calls needed)
            if response.stop_reason == "end_turn":
                # Response content is a list of blocks (text, tool_use, etc.)
                # When stop_reason is end_turn, we expect text blocks
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"\nAGENT: {block.text}")
                        return block.text

            # Case 2: Claude wants to use tools
            elif response.stop_reason == "tool_use":
                # Add Claude's response to the conversation history
                # This preserves what Claude said and which tools it wants to call
                messages.append({"role": "assistant", "content": response.content})

                # Execute each tool call and collect results
                tool_results = []
                for block in response.content:
                    # response.content can have multiple blocks:
                    # - text blocks (if Claude explains what it's doing)
                    # - tool_use blocks (the actual tool calls)
                    if block.type == "tool_use":
                        # Log the tool call for debugging
                        print(f"\nTool call: {block.name}")
                        print(f"Input: {json.dumps(block.input, indent=2)}")

                        try:
                            # Execute the tool function
                            result = self._execute_tool(block.name, block.input)
                            print(f"Result: {json.dumps(result, indent=2)}")

                            # Format result as a tool_result message to send back to Claude
                            # tool_use_id links this result to Claude's original request
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps(result),
                                }
                            )
                        except Exception as e:
                            # If tool execution fails, send error back to Claude
                            # Claude can often handle errors gracefully and explain them to the user
                            print(f"Tool error: {str(e)}")
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps({"error": str(e)}),
                                    "is_error": True,
                                }
                            )

                # Send tool results back to Claude as a "user" message
                # This allows Claude to see the results and continue reasoning
                # The loop will then make another request with the updated messages
                messages.append({"role": "user", "content": tool_results})
            else:
                # Handle unexpected stop reasons (shouldn't normally happen)
                print(f"Unexpected stop reason: {response.stop_reason}")
                break

        return "Max iterations reached"


def main():
    """Main entry point for running the agent.

    Creates a WeatherEnsembleAgent instance and runs a sample query
    to demonstrate the agent's capabilities. This is useful for:
    - Testing the agent during development
    - Demonstrating how to use the agent
    - Quick experimentation with different queries

    To run:
        python -m weather_agent.agent
    """
    # Create an agent instance
    agent = WeatherEnsembleAgent()

    # Run a sample query
    agent.run("What are the coordinates for Denver, Colorado?")


if __name__ == "__main__":
    main()
