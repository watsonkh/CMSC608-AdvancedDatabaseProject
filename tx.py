#!/usr/bin/env python3
import json
import os
import re
import argparse

default_file = "recipes_cleaned.jsonl"
default_output = "output.sql"

def load_file(file_path):
    """
    Load a JSONL file and return its content as a list of dictionaries.
    """
    with open(file_path, 'r') as file:
        data = [json.loads(line) for line in file]
    return data

def get_ingredients(data):
    # strip out all ingredients: these are "ingredients_decomposed" for each line
    food = {}
    for recipe in data:
        ingredients = recipe.get("ingredients_decomposed", {})
        for ingredient in ingredients.values():
            if "food" in ingredient:
                food.setdefault(ingredient["food"], ingredient["unit"])
    sql = []
    for ingredient,unit in food.items():
        unit = unit.lower()
        if re.search(r"s$", unit):
            unit = re.sub(r"s$", "", unit)
        if ingredient == "unknown":
            continue
        if re.search(r"^quart ", ingredient):
            ingredient = re.sub(r"^quart ", "", ingredient)
            unit = "quart"
        if unit == "large":
            unit = ""
        sql.append(f"INSERT INTO ingredient (name, baseUnit) VALUES ('{ingredient}', (SELECT id FROM unit WHERE name = '{unit}'));")
    return sql



def main():
    parser = argparse.ArgumentParser(description="Convert JSONL files to SQL")
    parser.add_argument("-f", "--file", type=str, default=default_file,
                        help="Path to the JSONL file")
    parser.add_argument("-o", "--output", type=str, default="output.sql",
                        help="Path to the output SQL file")
    args = parser.parse_args()
    file_path = args.file
    output_path = args.output

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return
    if not file_path.endswith(".jsonl"):
        print(f"File {file_path} is not a JSONL file.")
        return
    data = load_file(file_path)
    if not data:
        print(f"File {file_path} is empty.")
        return
    sql = get_ingredients(data)
    with open(output_path, 'w') as file:
        for string in sql:
            file.write(string + "\n")



if __name__ == "__main__":
    main()
