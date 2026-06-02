'''Orchestrate the agent flow'''

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from agent.tools.analytics import get_stats
from agent.tools.search import search_listings
from agent.tools.schemas import analytics_tool, search_tool
from openai import AsyncOpenAI
import json

tool_registry = {
    "get_stats": get_stats,
    "search_listings": search_listings,
}

tools = [analytics_tool, search_tool]
client = AsyncOpenAI()

async def agent(user_message: str, history: list[dict]) -> tuple[str, list]:
    messages = history[-10:] + [{"role": "user", "content": user_message}]
    listings = []

    while True:
        response = await client.chat.completions.create(
            model="gpt-4o",
            tools=tools,        # same tool schema as before, no changes needed
            messages=[
                {"role": "system", "content": "You are a real estate assistant for Sofia, Bulgaria. "
                    "Use the get_stats tool to answer market statistics questions. "
                    "Use the search_listings tool when the user wants to find or browse specific listings. "
                    "Always present prices in EUR. "
                    "When you call search_listings, respond with only 1 short sentence summarising what you found (e.g. neighbourhood, count). Do not list or describe individual properties. "
                    "IMPORTANT: neighbourhood names in the database are stored in Bulgarian Cyrillic. "
                    "Always translate neighbourhood names to Bulgarian Cyrillic before passing them to tools "
                    "(e.g. 'Lozenets' → 'Лозенец', 'Mladost' → 'Младост', 'Vitosha' → 'Витоша')."},
                    *messages
            ]
        )

        choice = response.choices[0]

        # LLM wants to call a tool
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)
                print(f"[tool_call] {tool_name}({tool_input})")

                tool_result = await tool_registry[tool_name](**tool_input)
                print(f"[tool_result] {tool_result}")

                if tool_name == "search_listings" and isinstance(tool_result, list):
                    listings = tool_result

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })

        # LLM is done
        elif choice.finish_reason == "stop":
            return choice.message.content, listings