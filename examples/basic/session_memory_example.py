"""
Example demonstrating session memory functionality.

This example shows how to use session memory to maintain conversation history
across multiple agent runs without manually handling .to_input_list().
"""

import asyncio
from agents import Agent, Runner, RunConfig


async def main():
    # Create an agent with session memory enabled
    agent = Agent(
        name="Assistant",
        instructions="Reply very concisely.",
        memory=True,  # Enable default SQLite session memory
    )

    # Define a session ID for this conversation
    session_id = "conversation_123"

    # Create run config with session ID
    run_config = RunConfig(session_id=session_id)

    print("=== Session Memory Example ===")
    print("The agent will remember previous messages automatically.\n")

    # First turn
    print("First turn:")
    print("User: What city is the Golden Gate Bridge in?")
    result = await Runner.run(
        agent, "What city is the Golden Gate Bridge in?", run_config=run_config
    )
    print(f"Assistant: {result.final_output}")
    print()

    # Second turn - the agent will remember the previous conversation
    print("Second turn:")
    print("User: What state is it in?")
    result = await Runner.run(agent, "What state is it in?", run_config=run_config)
    print(f"Assistant: {result.final_output}")
    print()

    # Third turn - continuing the conversation
    print("Third turn:")
    print("User: What's the population of that state?")
    result = await Runner.run(
        agent, "What's the population of that state?", run_config=run_config
    )
    print(f"Assistant: {result.final_output}")
    print()

    print("=== Conversation Complete ===")
    print("Notice how the agent remembered the context from previous turns!")
    print(
        "No need to manually handle .to_input_list() - session memory handles it automatically."
    )


if __name__ == "__main__":
    asyncio.run(main())
