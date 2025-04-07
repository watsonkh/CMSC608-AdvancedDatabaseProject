import llm_config
import os
import time
import pandas as pd
import google.generativeai as genai
from  google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv


def split_recipe(model: genai.GenerativeModel, prompt: str, generation_config, second_time=False):
    try:
        response = model.generate_content(prompt, generation_config=generation_config)
        print("Response generated")
        response_dict = response.to_dict()
        recipe_steps = {}
        for i, part in enumerate(response_dict["candidates"][0]["content"]["parts"]):
            named_entities = part["function_call"]["args"]["parts"]
            recipe_steps[i] = named_entities

        time.sleep(5)
        return recipe_steps

    except ResourceExhausted as e:
        print(e)
        print(f"Rate limit reached - waiting 55 seconds")
        time.sleep(55)
        if not second_time:
            return split_recipe(model, prompt, generation_config, second_time=True)
        return {}

def main(api_key: str, llm_model: str):
    genai.configure(api_key=api_key)

    function_declaration = {
        "name": llm_config.model_name,
        "description": llm_config.model_description,
        "parameters": llm_config.ingredient_schema
    }
    tool_config = {
        "function_declarations": [function_declaration]
    }
    generation_config = {
        "max_output_tokens": 2048,
        "temperature": 0.2,
        "top_p": 1,
        "top_k": 1
    }


    model = genai.GenerativeModel(model_name=llm_model,
                                   tools=[tool_config],
                                    system_instruction=llm_config.system_instruction)

    recipe_fp = "recipe_semi_cleaned.jsonl"
    recipes_df = pd.read_json(recipe_fp, lines=True)
    recipes_df["ingredients_decomposed"] = recipes_df["ingredients"].apply(lambda x: split_recipe(model, x, generation_config))
    recipes_df.to_json("recipes_cleaned_2.jsonl", orient="records", lines=True)

if __name__ == "__main__":
    load_dotenv()
    llm_model = "gemini-1.5-flash-002"
    gemini_api_key = os.getenv("API_KEY")
    main(gemini_api_key, llm_model)

