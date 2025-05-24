"""
Example demonstrating session memory functionality.

This example shows how to use session memory to maintain conversation history
across multiple agent runs without manually handling .to_input_list().
"""

import asyncio
from agents import Agent, Runner, RunConfig, SQLiteSessionMemory


async def main():
    # Create an agent
    agent = Agent(
        name="Assistant",
        instructions="Reply very concisely.",
    )

    # Create a session memory instance that will persist across runs
    memory = SQLiteSessionMemory()

    # Define a session ID for this conversation
    session_id = "conversation_123"

    # Create run config with session memory and session ID
    run_config = RunConfig(
        memory=memory, session_id=session_id  # Use our session memory instance
    )

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
    print("Session memory in RunConfig handles conversation history automatically.")


if __name__ == "__main__":
    asyncio.run(main())
