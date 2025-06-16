import argparse
import asyncio
import random

from agents import Agent, GenerateDynamicPromptData, Runner


class DynamicContext:
    def __init__(self):
        self.poem_style = random.choice(["limerick", "palindrome", "haiku", "ballad"])
        print(f"[debug] DynamicContext initialized with poem_style: {self.poem_style}")


async def _get_dynamic_prompt(data: GenerateDynamicPromptData):
    ctx: DynamicContext = data.context.context
    return {
        "id": "pmpt_6850729e8ba481939fd439e058c69ee004afaa19c520b78b",
        "version": "1",
        "variables": {
            "poem_style": ctx.poem_style,
        },
    }


async def dynamic_prompt():
    context = DynamicContext()

    agent = Agent(
        name="Assistant",
        prompt=_get_dynamic_prompt,
    )

    result = await Runner.run(agent, "Tell me about recursion in programming.", context=context)
    print(result.final_output)


async def static_prompt():
    agent = Agent(
        name="Assistant",
        prompt={
            "id": "pmpt_6850729e8ba481939fd439e058c69ee004afaa19c520b78b",
            "version": "1",
            "variables": {
                "poem_style": "limerick",
            },
        },
    )

    result = await Runner.run(agent, "Tell me about recursion in programming.")
    print(result.final_output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dynamic", action="store_true")
    args = parser.parse_args()

    if args.dynamic:
        asyncio.run(dynamic_prompt())
    else:
        asyncio.run(static_prompt())
