ingredient_schema = {
    "type": "object",
    "properties": {
        "ingredient": {
            "type": "string",
            "description": "The original ingredient line"
        },
        "parts": {
            "type": "object",
            "properties": {
                "quantity": {
                    "type": "string",
                    "description": "The quantity of the ingredient"
                },
                "unit": {
                    "type": "string",
                    "description": "The measurement unit"
                },
                "food": {
                    "type": "string",
                    "description": "The name of the food item"
                }
            },
            "required": ["quantity", "unit", "food"]
        }
    },
    "required": ["ingredient", "parts"]
}

system_instruction = """
You are a data extraction assistant. Given a list of recipe ingredient lines, extract the following parts for each:

- QUANTITY (numeric or fraction)
- UNIT (e.g., cups, tbsp, ounces)
- FOOD (main ingredient or item)
"""

model_description = "Parse quantity, unit, and food from a recipe ingredient line"
model_name = "parse_ingredients"