# Session Memory

The Agents SDK provides built-in session memory to automatically maintain conversation history across multiple agent runs, eliminating the need to manually handle `.to_input_list()` between turns.

Session memory stores conversation history across agent runs, allowing agents to maintain context without requiring explicit manual memory management. This is particularly useful for building chat applications or multi-turn conversations where you want the agent to remember previous interactions.

## Quick start

```python
from agents import Agent, Runner, SQLiteSessionMemory

# Create agent
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
)

# Create a session memory instance
memory = SQLiteSessionMemory()

# First turn
result = await Runner.run(
    agent,
    "What city is the Golden Gate Bridge in?",
    memory=memory,
    session_id="conversation_123"
)
print(result.final_output)  # "San Francisco"

# Second turn - agent automatically remembers previous context
result = await Runner.run(
    agent,
    "What state is it in?",
    memory=memory,
    session_id="conversation_123"
)
print(result.final_output)  # "California"

# Also works with synchronous runner
result = Runner.run_sync(
    agent,
    "What's the population?",
    memory=memory,
    session_id="conversation_123"
)
print(result.final_output)  # "Approximately 39 million"
```

## How it works

When session memory is enabled:

1. **Before each run**: The runner automatically retrieves the conversation history for the given `session_id` and prepends it to the input messages.
2. **After each run**: All new messages generated during the run (user input, assistant responses, tool calls, etc.) are automatically stored in the session memory.
3. **Context preservation**: Each subsequent run in the same session includes the full conversation history, allowing the agent to maintain context.

This eliminates the need to manually call `.to_input_list()` and manage conversation state between runs.

## Memory operations

### Basic operations

Session memory supports several operations for managing conversation history:

```python
from agents import SQLiteSessionMemory

memory = SQLiteSessionMemory("conversations.db")
session_id = "user_123"

# Get all messages in a session
messages = await memory.get_messages(session_id)

# Add new messages to a session
new_messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]
await memory.add_messages(session_id, new_messages)

# Remove and return the most recent message
last_message = await memory.pop_message(session_id)
print(last_message)  # {"role": "assistant", "content": "Hi there!"}

# Clear all messages from a session
await memory.clear_session(session_id)
```

### Using pop_message for corrections

The `pop_message` method is particularly useful when you want to undo or modify the last message in a conversation:

```python
from agents import Agent, Runner, SQLiteSessionMemory

agent = Agent(name="Assistant")
memory = SQLiteSessionMemory()
session_id = "correction_example"

# Initial conversation
result = await Runner.run(
    agent,
    "What's 2 + 2?",
    memory=memory,
    session_id=session_id
)
print(f"Agent: {result.final_output}")

# User wants to correct their question
user_message = await memory.pop_message(session_id)  # Remove user's question
assistant_message = await memory.pop_message(session_id)  # Remove agent's response

# Ask a corrected question
result = await Runner.run(
    agent,
    "What's 2 + 3?",
    memory=memory,
    session_id=session_id
)
print(f"Agent: {result.final_output}")
```

## Memory options

### No memory (default)

```python
# Default behavior - no session memory
result = await Runner.run(agent, "Hello")
```

### SQLite memory

```python
from agents import SQLiteSessionMemory

# In-memory database (lost when process ends)
memory = SQLiteSessionMemory()

# Persistent file-based database
memory = SQLiteSessionMemory("conversations.db")

# Use the memory with session IDs
result = await Runner.run(
    agent,
    "Hello",
    memory=memory,
    session_id="user_123"
)
```

### Multiple sessions

```python
from agents import Agent, Runner, SQLiteSessionMemory

memory = SQLiteSessionMemory("conversations.db")
agent = Agent(name="Assistant")

# Different session IDs maintain separate conversation histories
result1 = await Runner.run(
    agent,
    "Hello",
    memory=memory,
    session_id="user_123"
)
result2 = await Runner.run(
    agent,
    "Hello",
    memory=memory,
    session_id="user_456"
)
```

## Custom memory implementations

You can implement your own session memory by creating a class that follows the [`SessionMemory`][agents.memory.session_memory.SessionMemory] protocol:

````python
from agents.memory import SessionMemory
from typing import List

class MyCustomMemory:
    """Custom memory implementation following the SessionMemory protocol."""

    async def get_messages(self, session_id: str) -> List[dict]:
        """Retrieve conversation history for the session."""
        # Your implementation here
        pass

    async def add_messages(self, session_id: str, messages: List[dict]) -> None:
        """Store new messages for the session."""
        # Your implementation here
        pass

    async def pop_message(self, session_id: str) -> dict | None:
        """Remove and return the most recent message from the session."""
        # Your implementation here
        pass

    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for the session."""
        # Your implementation here
        pass

# Use your custom memory
agent = Agent(name="Assistant")
result = await Runner.run(
    agent,
    "Hello",
    memory=MyCustomMemory(),
    session_id="my_session"
)

## Requirements and validation

### session_id requirement

When session memory is enabled, you **must** provide a `session_id`. If you don't, the runner will raise a `ValueError`:

```python
from agents import Agent, Runner, SQLiteSessionMemory

agent = Agent(name="Assistant")
memory = SQLiteSessionMemory()

# This will raise ValueError: "session_id is required when memory is enabled"
result = await Runner.run(agent, "Hello", memory=memory)

# This works correctly
result = await Runner.run(
    agent,
    "Hello",
    memory=memory,
    session_id="my_session"
)
```

## Best practices

### Session ID naming

Use meaningful session IDs that help you organize conversations:

-   User-based: `"user_12345"`
-   Thread-based: `"thread_abc123"`
-   Context-based: `"support_ticket_456"`

### Memory persistence

-   Use in-memory SQLite (`SQLiteSessionMemory()`) for temporary conversations
-   Use file-based SQLite (`SQLiteSessionMemory("path/to/db.sqlite")`) for persistent conversations
-   Consider implementing custom memory backends for production systems (Redis, PostgreSQL, etc.)

### Session management

```python
# Clear a session when conversation should start fresh
await memory.clear_session("user_123")

# Different agents can share the same session memory
support_agent = Agent(name="Support")
billing_agent = Agent(name="Billing")

# Both agents will see the same conversation history
result1 = await Runner.run(
    support_agent,
    "Help me with my account",
    memory=memory,
    session_id="user_123"
)
result2 = await Runner.run(
    billing_agent,
    "What are my charges?",
    memory=memory,
    session_id="user_123"
)
```

## Complete example

Here's a complete example showing session memory in action:

```python
import asyncio
from agents import Agent, Runner, SQLiteSessionMemory


async def main():
    # Create an agent
    agent = Agent(
        name="Assistant",
        instructions="Reply very concisely.",
    )

    # Create a session memory instance that will persist across runs
    memory = SQLiteSessionMemory("conversation_history.db")

    # Define a session ID for this conversation
    session_id = "conversation_123"

    print("=== Session Memory Example ===")
    print("The agent will remember previous messages automatically.\n")

    # First turn
    print("First turn:")
    print("User: What city is the Golden Gate Bridge in?")
    result = await Runner.run(
        agent,
        "What city is the Golden Gate Bridge in?",
        memory=memory,
        session_id=session_id
    )
    print(f"Assistant: {result.final_output}")
    print()

    # Second turn - the agent will remember the previous conversation
    print("Second turn:")
    print("User: What state is it in?")
    result = await Runner.run(
        agent,
        "What state is it in?",
        memory=memory,
        session_id=session_id
    )
    print(f"Assistant: {result.final_output}")
    print()

    # Third turn - continuing the conversation
    print("Third turn:")
    print("User: What's the population of that state?")
    result = await Runner.run(
        agent,
        "What's the population of that state?",
        memory=memory,
        session_id=session_id
    )
    print(f"Assistant: {result.final_output}")
    print()

    print("=== Conversation Complete ===")
    print("Notice how the agent remembered the context from previous turns!")
    print("Session memory automatically handles conversation history.")


if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

For detailed API documentation, see:

-   [`SessionMemory`][agents.memory.SessionMemory] - Protocol interface
-   [`SQLiteSessionMemory`][agents.memory.SQLiteSessionMemory] - SQLite implementation
-   [`RunConfig.memory`][agents.run.RunConfig.memory] - Run configuration
-   [`RunConfig.session_id`][agents.run.RunConfig.session_id] - Session identifier
````
