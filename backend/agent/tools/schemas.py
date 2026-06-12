# tools/schemas.py
# WIP: Add historical price data - p/neighbourhood, city, etc.
analytics_tool = {
    "type": "function",
    "function": {
        "name": "get_stats",
        "description": """Get market statistics for real estate listings.
            Use this when the user asks about average price, median price, 
            price per sqm, or number of listings — either overall or for a specific neighborhood. 
            Also be ready to compare prices between neighbourhoods.""",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["avg_price", "median_price", "avg_price_sqm", "listing_count", "min_price", "max_price", "min_price_sqm", "max_price_sqm"],
                    "description": "The statistic to compute"
                },
                "filters": {
                    "type": "object",
                    "description": "Filter by the following: neighbourhood, nr_of_rooms, akt16, broker_commision, type_of_estate (in Bulgarian Cyrilic, always lower cap), energy_class."
                    "Neighbourhoods MUST be in Bulgarian Cyrillic as stored in the DB, e.g. 'Лозенец', 'Младост', 'Витоша'. "
                    "Note there're areas with many numbers, e.g. Люлин 1,2 ..., same holds for Дружба, Младост, Надежда. In case no number is provided, aggregate for the entire area."
                    ""
                }
            },
            "required": ["metric"]
        }
    }
}

search_tool = {
    "type": "function",
    "function": {
        "name": "search_listings",
        "description": """Search for real estate listings matching the user's criteria.
            Use this when the user wants to find, browse, or get specific listings — e.g. '2-bedroom apartment in Lozenets under 150k'.
            Returns the top matching listings with price, size, neighbourhood, and a link.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user's search query in their original language"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of listings to return. Defaults to 5.",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}
