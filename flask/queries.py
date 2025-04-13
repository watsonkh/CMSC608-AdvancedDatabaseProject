# This Python script contains all of the queries used inside app.py 
# Hopefully this will make app.py a bit cleaner

image_similarity_query = """\
    SELECT image.id, recipeId, imageLocation, \
       (embedding <=> %s::vector(512)) AS cosine_distance, \
       (1 - (embedding <=> %s::vector(512)) / 2) AS cosine_similarity, \
       recipe.name as recipe_name
    FROM image \
    JOIN recipe on image.recipeid = recipe.id \
    WHERE embedding IS NOT NULL \
    ORDER BY embedding <=> %s::vector(512) \
    LIMIT 5;
"""

recipe_steps_query = """\
    SELECT recipe_ingredient.id, unit, recipeid, displayorder,quantity, denominator, ingredient.name, unit.name as unit_name
    FROM recipe_ingredient 
    JOIN ingredient ON recipe_ingredient.ingredientid = ingredient.id
    JOIN unit ON recipe_ingredient.unit = unit.id
    WHERE recipeId = %s;
"""