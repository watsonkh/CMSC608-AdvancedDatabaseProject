# This Python script contains all of the queries used inside app.py 
# Hopefully this will make app.py a bit cleaner

image_similarity_query = """\
    SELECT image.id, recipeId, imageLocation, \
       (embedding <=> %s::vector(512)) AS cosine_distance, \
       ((1 - cosine_distance) / 2) AS cosine_similarity, \
       recipe.name as recipe_name
    FROM image \
    JOIN recipe on image.recipeid = recipe.id \
    WHERE embedding IS NOT NULL \
    ORDER BY cosine_distance \
    LIMIT 5;
"""

# recipe_steps_query = """\
#     SELECT recipe_ingredient.id, unit, recipeid, displayorder,quantity, denominator, ingredient.name, unit.name as unit_name
#     FROM recipe_ingredient 
#     JOIN ingredient ON recipe_ingredient.ingredientid = ingredient.id
#     JOIN unit ON recipe_ingredient.unit = unit.id
#     WHERE recipeId = %s;
# """

recipe_steps_query = """
        select s.description, s.imagelocation
           from step s
           inner join recipe r on s.recipeId = r.id
           where r.id = %s
           order by s.displayorder;
 """

recipe_ingredients_query = """
        select ri.quantity as quantity, ri.denominator as denominator, u.notation as notation, i.\"name\" as name, u.unitType as unitType
          from recipe_ingredient ri
          inner join recipe r on ri.recipeId = r.id
          inner join ingredient i on ri.ingredientid = i.id
          inner join unit u on ri.unit = u.id
          where r.id = %s
          order by ri.displayorder;
"""
