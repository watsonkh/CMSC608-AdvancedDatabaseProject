# This Python script contains all of the queries used inside app.py 
# Hopefully this will make app.py a bit cleaner

image_similarity_query = """\
    SELECT id, recipeId, imageLocation, \
       (embedding <=> %s::vector(512)) AS cosine_distance, \
       (1 - (embedding <=> %s::vector(512)) / 2) AS cosine_similarity \
    FROM image \
    WHERE embedding IS NOT NULL \
    ORDER BY embedding <=> %s::vector(512) \
    LIMIT 5;
"""