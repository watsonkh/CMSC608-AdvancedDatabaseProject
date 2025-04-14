#!python

import torch
import psycopg2
import psycopg2.extras
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import os
import hashlib
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CACHE_DIR = "static/image_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def query_image_urls(conn: psycopg2.extensions.connection):
    """
    Queries for all image urls in recipe and step tables in locally running 
    PostgreSQL database.
    Returns tuple[list, list]
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, mainImage FROM recipe")
    recipes = cur.fetchall()
    recipes = [[id, img_url, get_image_from_url(img_url, verbose=True)]
                for id, img_url in recipes if img_url != "None"]
    cur.execute("SELECT recipeId, imageLocation FROM step")
    steps = cur.fetchall()
    steps = [[id, img_url, get_image_from_url(img_url, verbose=True)]
              for id, img_url in steps if img_url is not None]
    cur.close()
    return (recipes, steps)

def get_image_from_url(url: str, verbose=False) -> Image.Image:
    """
    Downloads all images from urls queried from PostgreSQL DB.
    Stores them in CACHE_DIR folder to prevent having to redownload old files.
    All images are resized to 256x256, so this means all images queried in a similarity search
    should also be resized to 256x256.
    """
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{url_hash}.jpg")

    if os.path.exists(cache_path):
        if verbose:
            print(f"Loading cached image for URL: {url[:75]}...")
        return Image.open(cache_path).convert("RGB").resize(size=[256, 256])
    else:
        if verbose:
            print(f"Downloading img from url: {url[:75]}...")
        img = Image.open(requests.get(url, stream=True, timeout=30).raw).convert("RGB")
        img = img.resize(size=[256, 256])
        img.save(cache_path, format="JPEG")
        return img


def init_CLIP():
    """
    Initializes CLIP models needed to produce embeddings.
    Returns tuple[CLIPModel, CLIPProcessor]
    """
    print("Initializing CLIP model - this may take a while")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return (model, processor)

def create_embedding(img_list: list[Image.Image], model: CLIPModel, processor: CLIPProcessor):
    """
    Given list of Pillow Images, produces list of 512 length embeddings/vectors.
    Uses CLIPModel and ClipProcessor to produce embeddings.
    Returns torch Tensor
    """
    inputs = processor(images=img_list, return_tensors="pt", padding=True)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    return image_features.cpu().numpy()

def get_db_connection(default_port=5432):
    """
    Connects to local Postgres DB, provided that you have set a .env file.
    Should we have this reused in two different places (app.py, embeddings.py)??
    """
    conn = psycopg2.connect(
        host=os.getenv("HOST"),
        database=os.getenv("DATABASE"),
        port=os.getenv("PORT", default_port),
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD")
    )
    return conn

def replace_img_with_embedding(sql_list, embeddings):
    for sql_row, embedding in zip(sql_list, embeddings):
        emb_list = embedding.tolist()
        sql_row[2] = emb_list
    
def populate_image_table(recipes, steps, conn: psycopg2.extensions.connection):
    """
    Inserts generated image embeddings from Recipe and Step tables into Image table.
    Connects to PostgreSQL DB with pyscopg2 connection.
    """
    print("Populating image table with embeddings!")
    cur = conn.cursor()
    recipes.extend(steps)
    for recipe in recipes:
        recipeId = recipe[0]
        imageLocation = recipe[1]
        imageEmbedding = recipe[2]
        cur.execute("INSERT INTO image (recipeId, imageLocation, embedding) VALUES (%s, %s, %s);",
                    (recipeId, imageLocation, imageEmbedding)
        )
    conn.commit()
    cur.close()


def query_recipe_descriptions(conn: psycopg2.extensions.connection):
    """
    Queries for all recipe descriptions in locally running PostgreSQL database.
    Returns list of tuples (id, description)
    """
    # Add recipe.name, recipe.description, step.description, ingredient.name into on string, then embed that
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, description, name FROM recipe")
    recipes = cur.fetchall()
    for (i, (id, desc, name)) in enumerate(recipes):
        cur.execute(f"SELECT s.description from step s WHERE s.recipeid = {id}")
        descriptions = cur.fetchall()
        cur.execute(f"select i.name from recipe_ingredient ri inner join ingredient i on i.id = ri.ingredientid WHERE ri.recipeid = {id}")
        ingredients = cur.fetchall()

        recipes[i][2] = desc + " " + name + " " + " ".join([d[0] for d in descriptions]) + " " + " ".join([i[0] for i in ingredients])
    cur.close()
    return recipes

def create_text_embedding(descriptions: list[str]):
    """
    Given list of strings, produces list of 768 length embeddings/vectors.
    Uses `SentenceTransformer` to produce embeddings.
    """
    text_model = SentenceTransformer('all-mpnet-base-v2')
    return list(text_model.encode(descriptions, normalize_embeddings=True))

def populate_text_embeddings(recipe_info, conn: psycopg2.extensions.connection):
    """
    Inserts generated text embeddings from Recipe and Step tables into Text table.
    Connects to PostgreSQL DB with psycopg2 connection.
    """
    print("Populating text table with embeddings!")
    cur = conn.cursor()
    for recipe in recipe_info:
        recipeId = recipe[0]
        textEmbedding = recipe[1].astype(float).tolist()
        cur.execute("INSERT INTO recipe_embeddings (recipeid, description_embedding) VALUES (%s, %s);", (recipeId, textEmbedding))



def main():
    conn = get_db_connection()

    # text embeddings
    descriptions = query_recipe_descriptions(conn)
    ids = [recipe[0] for recipe in descriptions]
    text_descriptions = [recipe[1] for recipe in descriptions]
    embeddings = create_text_embedding(text_descriptions)
    info = [(ids[i], embeddings[i]) for i in range(len(descriptions))]
    # print(info[0])
    # print(descriptions)
    # print(len(info))
    # return
    populate_text_embeddings(info, conn)

    model, processor = init_CLIP()

    recipes, steps = query_image_urls(conn)
    print("Creating embeddings for mainImage urls in Recipe table")
    print(recipes)
    recipe_img_embeddings = create_embedding(
        [recipe[2] for recipe in recipes],
        model, 
        processor
    )
    print("Creating embeddings for imageLocation urls in Step table")
    step_img_embeddings = create_embedding(
        [step[2] for step in steps],
        model,
        processor
    )
    print("Updating database with embeddings")
    replace_img_with_embedding(recipes, recipe_img_embeddings)
    replace_img_with_embedding(steps, step_img_embeddings)
    populate_image_table(recipes, steps, conn)
    print("Done")
    conn.close()


if __name__ == "__main__":
    load_dotenv(override=True)
    main()
