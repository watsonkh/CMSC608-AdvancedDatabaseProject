#!/usr/bin/env python3
import json
import os
import re
import argparse

default_file = "recipes_cleaned.jsonl"
default_output = "output.sql"

def esc(s):
    return s.replace("'", "''")

def singularize(s):
    if s.endswith('s'):
        if s.endswith('tomatoes'):
            return s.replace('tomatoes', 'tomato')
        if s.endswith('potatoes'):
            return s.replace('potatoes', 'potato')
        return s[:-1]
    return s

def replace_unicode(text):
    replacements = {"½": "1/2", "⅓": "1/3", "¼": "1/4"}
    for unicode_char, ascii_str in replacements.items():
        text = text.replace(unicode_char, ascii_str)
    return text

def fudge(food, quantity, unit):
    """
    Fudge the food name, quantity, and unit based on some specific rules.
    """
    if quantity == "" and unit == "":
        return food, 1, ""
    if food == "thyme sprig":
        return "thyme", 3, "sprig"
    if m := re.search(r"\d+( to |-)(\d+)", quantity):
        return food, m.group(2), unit
    if unit == "6-inch piece":
        return food, 6, "inch"
    if quantity == "Pinch":
        return food, 1, "pinch"
    if quantity == "8-10":
        return food, 10, ""
    if food == "evaporated milk":
        return food, 1, "can"
    if quantity == "One 3-pound":
        return food, 3, "pound"
    raise ValueError(f"Unknown food: {food}, quantity: {quantity}, unit: {unit}")

def load_file(file_path):
    """
    Load a JSONL file and return its content as a list of dictionaries.
    """
    with open(file_path, 'r') as file:
        data = [json.loads(line) for line in file]
    return data

conversions = {
        "large": "",
        "14-ounce": "ounce",
        "12-ounce": "ounce",
        "dashe": "dash",
        "each": "",
        "pepper": "",
        "scallion": "",
        "small": "",
        "medium": ""}
sizes = { "large", "small", "medium" }

def convert(food, unit):
    unit = singularize(unit).lower()
    if unit in conversions:
        unit = conversions[unit]
        if unit in sizes:
            food = unit + " " + food
    if re.search(r"^quart ", food):
        food = re.sub(r"^quart ", "", food)
        unit = "quart"
    return food, unit

def get_ingredients(data):
    # strip out all ingredients: these are "ingredients_decomposed" for each line
    foods = {}
    simple_names = set()
    for recipe in data:
        ingredients = recipe.get("ingredients_decomposed", {})
        for ingredient in ingredients.values():
            if "food" in ingredient:
                food = singularize(ingredient["food"])
                unit = ingredient["unit"]
                unit = unit.lower()
                food, unit = convert(food, unit)
                simple_name = food.lower()
                if simple_name in simple_names:
                    if food in foods:
                        print(f"Duplicate ingredient with different case found: {ingredient['food']}")
                    continue
                foods.setdefault(food, unit)
    sql = "INSERT INTO ingredient (name, baseUnit) VALUES\n"
    sql_strs = []
    for ingredient,unit in foods.items():
        if ingredient == "unknown":
            continue
        sql_strs.append(f"  ('{esc(singularize(ingredient))}', (SELECT id FROM unit WHERE name = '{unit}'))")
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
    sql_str = f"INSERT INTO recipe_ingredient (recipeId, ingredientId, displayOrder, unit, quantity, denominator) VALUES\n"
    sql_strs = []
    for recipe in data:
        ingredients = recipe.get("ingredients_decomposed", {})
        for order,ingredient in ingredients.items():
            food = singularize(ingredient["food"])
            quantity = ingredient["quantity"]
            unit0 = ingredient["unit"]
            food, unit = convert(food, unit0)
            if quantity == "":
                quantity = "1"
                if unit != "":
                    print(f"Warning: ingredient {food} has empty quantity for unit '{unit}': using 1")
            quantity = replace_unicode(quantity)
            frac = re.search(r"([ 0-9]+)/(\d+)", quantity)
            numerator = ""
            denominator = "NULL"
            if om := re.search(r"(\d+)-ounce", unit0):
                if not unit0.endswith(" can"):
                    numerator = om.group(1)
            if frac:
                denominator = frac.group(2)
                num = frac.group(1)
                if m := re.search(r"(\d+) +(\d+)", num):
                    a = m.group(1)
                    b = m.group(2)
                    numerator = int(denominator) * int(a) + int(b)
                else:
                    numerator = num
            else:
                try:
                    numerator = int(quantity)
                except ValueError:
                    try:
                        food, numerator, unit = fudge(food, quantity, unit)
                    except ValueError:
                        print(f"Error: ingredient {food} has unknown quantity {quantity}, in {recipe['name']}")
                        raise
            sql_strs.append(f"  ((SELECT id FROM recipe WHERE name = '{esc(recipe['name'])}'),\n"
                            f"   (SELECT id FROM ingredient WHERE name = '{esc(food)}'), {order},\n"
                            f"   (SELECT id FROM unit WHERE name = '{unit}'), {numerator}, {denominator})")
    return [sql_str + ",\n".join(sql_strs) + ";"]

def get_steps(data):
    sql_str = f"INSERT INTO step (recipeId, displayOrder, description, imageLocation) VALUES\n"
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
