'''Orchestrate the agent flow'''

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from agent.tools.analytics import get_stats
from agent.tools.search import search_listings
from agent.tools.find_deals import find_deals
from agent.tools.schemas import analytics_tool, search_tool, find_deals_tool
from openai import AsyncOpenAI
import json

# the actual functionlity of the tools
tool_registry = {
    "get_stats": get_stats,
    "search_listings": search_listings,
    "find_deals": find_deals
}

# put the schematics of the tools
tools = [analytics_tool, search_tool, find_deals_tool]
client = AsyncOpenAI()

async def agent(user_message: str, history: list[dict]) -> tuple[str, list]:
    
    # keep last 10 messages as history
    messages = history[-10:] + [{"role": "user", "content": user_message}]
    listings = []

    while True:
        response = await client.chat.completions.create(
            model="gpt-4o",
            tools=tools,       
            messages=[  
                {
                "role": "system", 
                "content": "You are a real estate assistant for Sofia, Bulgaria. "
                    "Use the get_stats tool to answer market statistics questions. "
                    "Use the search_listings tool when the user wants to find or browse listings by location, size, or price — but NOT for deal-hunting. "
                    "Use the find_deals tool when the user asks for deals, undervalued/underpriced apartments, investment opportunities, good ROI, or rental yield. "
                    "When unsure between search_listings and find_deals, prefer find_deals if the query contains any value-judgement (cheap, good deal, worth it, investment)."
                    "Always present prices in EUR. "
                    "The default estate type are appartments"
                    "When you call search_listings, respond with only 1 short sentence summarising what you found (e.g. neighbourhood, count). Do not list or describe individual properties. "
                    "IMPORTANT: neighbourhood names in the database are stored in Bulgarian Cyrillic. "
                    "Always translate neighbourhood names to Bulgarian Cyrillic before passing them to tools. The entire data is from Sofia, BG."
                    "(e.g. 'Lozenets' → 'Лозенец', 'Mladost' → 'Младост', 'Vitosha' → 'Витоша')."
                },
                *messages
            ]
        )

        choice = response.choices[0]
        print(f"[AGENT] finish_reason: {choice.finish_reason}")

        # LLM wants to call a tool
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)
                print(f"[TOOL SELECTED] {tool_name}")        # dsiplay which tool it picked & the input to the tool
                print(f"[TOOL INPUT] {tool_input}") 

                tool_result = await tool_registry[tool_name](**tool_input)
                print(f"[TOOL RESULT] {len(tool_result)}")

                if tool_name in ("search_listings", "find_deals") and isinstance(tool_result, list):
                    listings = tool_result
                    tool_summary = f"Found {len(tool_result)} listings."
                else:
                    tool_summary = str(tool_result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_summary
                })

        # LLM is done
        elif choice.finish_reason == "stop":
            final = choice.message.content
            print(f"[FINAL RESPONSE] {final}")
            return final, listings