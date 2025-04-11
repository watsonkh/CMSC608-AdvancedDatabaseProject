#!/usr/bin/env python3
import json
import os
import re
import argparse

default_file = "recipes_cleaned.jsonl"
default_output = "output.sql"

def esc(s):
    return s.replace("'", "''")

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
    simple_names = set()
    for recipe in data:
        ingredients = recipe.get("ingredients_decomposed", {})
        for ingredient in ingredients.values():
            if "food" in ingredient:
                simple_name = ingredient["food"].lower()
                if simple_name in simple_names:
                    if ingredient["food"] in food:
                        print(f"Duplicate ingredient with different case found: {ingredient['food']}")
                    continue
                food.setdefault(ingredient["food"], ingredient["unit"])
    sql = "INSERT INTO ingredient (name, baseUnit) VALUES\n"
    sql_strs = []
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
        sql_strs.append(f"  ('{esc(ingredient)}', (SELECT id FROM unit WHERE name = '{unit}'))")
    return [sql + ",\n".join(sql_strs) + ";"]

def get_recipes(data):
    sql = "INSERT INTO recipe (name, description, servings, mainImage) VALUES\n"
    sql_strs = []
    for recipe in data:
        name = recipe["name"]
        description = recipe["description"]
        servings = recipe["servings"]
        mainImage = recipe["mainImageUrl"]
        sql_strs.append(f"   ('{esc(name)}', '{esc(description)}', '{servings}', '{mainImage}')")
    return [sql + ",\n".join(sql_strs) + ";"]

def get_recipe_ingredients(data):
    sql_str = f"INSERT INTO recipe_ingredient (recipe_id, ingredient_id, order, unitId, quantity, denominator) VALUES\n"
    sql_strs = []
    for recipe in data:
        ingredients = recipe.get("ingredients_decomposed", {})
        for order,ingredient in ingredients.items():
            food = ingredient["food"]
            quantity = ingredient["quantity"]
            unit = ingredient["unit"]
            frac = re.search(r"([ 0-9]+)/(\d+)", quantity)
            numerator = ""
            denominator = "NULL"
            if frac:
                denominator = frac.group(2)
                num = frac.group(1)
                m = re.search(r"(\d+) +(\d+)", num)
                if m:
                    a = m.group(1)
                    b = m.group(2)
                    numerator = int(denominator) * int(a) + int(b)
                else:
                    numerator = num
            else:
                numerator = quantity
                denominator = "NULL"
            sql_strs.append(f"  ((SELECT id FROM recipe WHERE name = '{esc(recipe['name'])}'),\n   (SELECT id FROM ingredient WHERE name = '{esc(food)}'), {order},\n"
                            f"   (SELECT id FROM unit WHERE name = '{unit}'), {numerator}, {denominator})")
    return [sql_str + ",\n".join(sql_strs) + ";"]

def get_steps(data):
    sql_str = f"INSERT INTO step (recipeId, order, description, image) VALUES\n"
    sql = []
    for recipe in data:
        steps = recipe["steps"]
        recipe_name = recipe["name"]
        for step in steps:
            order = step["order"]
            description = step["description"]
            image = step["image_url"]
            imagev = "NULL"
            if image and image != "":
                imagev = f"'{image}'"
            sql.append(f"  ((SELECT id FROM recipe WHERE name = '{esc(recipe_name)}'),\n   {order}, '{esc(description)}', {imagev})")
    return [sql_str + ",\n".join(sql) + ";"]


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
    sql.append("\n")
    sql.extend(get_recipes(data))
    sql.append("\n")
    sql.extend(get_recipe_ingredients(data))
    sql.append("\n")
    sql.extend(get_steps(data))
    with open(output_path, 'w') as file:
        for string in sql:
            file.write(string + "\n")



if __name__ == "__main__":
    main()
