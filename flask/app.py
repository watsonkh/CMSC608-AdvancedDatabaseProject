import os
import imghdr
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image
from embeddings import init_CLIP, create_embedding
from queries import image_similarity_query

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
DEFAULT_DB_PORT = 5432

load_dotenv(override=True)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("HOST"),
        database=os.getenv("DATABASE"),
        port=os.getenv("PORT", DEFAULT_DB_PORT),
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD")
    )
    return conn

@app.route('/image_search', methods=['GET', 'POST'])
def image_search():
    """
    Used file upload skeleton code from:
    https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
    Handles 
    """
    if request.method == 'POST':
        print("[DEBUG] Received POST Request")
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        print(file.filename)
        if file.filename == "":
            flash('No selected file')
            return redirect(request.url)
        
        # If valid file and has image file extension like .jpg
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            img_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"[DEBUG] Saving file to: {img_filepath}")
            file.save(img_filepath)

            # If given filepath is valid image
            if imghdr.what(img_filepath):
                model, processor = init_CLIP()
                img = Image.open(img_filepath).convert("RGB").resize(size=[256, 256])
                img_embedding = create_embedding([img], model, processor)[0].tolist()
                conn = get_db_connection()
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute(image_similarity_query, (img_embedding, img_embedding, img_embedding))
                results = cur.fetchall()
                print(results)
                cur.close()
                conn.close()
                return render_template('image_result.html', filename=filename, similar_images=results)
            else:
                os.remove(img_filepath)
                flash('Uploaded file is not a valid image')
                return redirect(request.url)
        else:
            flash('File type not allowed!')
            return redirect(request.url)
    return render_template("image_search.html")


@app.route('/recipe/')
@app.route('/recipe/<int:id>')
def recipe(id=None):
    if id is None:
        return render_template('recipe.html', recipe_id=None)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(f"SELECT * FROM recipe WHERE id = %s;", (id,))
    recipe = cur.fetchone()
    cur.execute("""
        select ri.quantity as quantity, ri.denominator as denominator, u.notation as notation, i.\"name\" as name, u.unitType as unitType
          from recipe_ingredient ri
          inner join recipe r on ri.recipeId = r.id
          inner join ingredient i on ri.ingredientid = i.id
          inner join unit u on ri.unit = u.id
          where r.id = %s
          order by ri.displayorder;
    """, (id,))
    ingredients = cur.fetchall()
    for ingredient in ingredients:
        if ingredient['denominator'] is not None:
            ingredient['quantity'] = f"{ingredient['quantity']} / {ingredient['denominator']}"
        elif ingredient['quantity'] == 1 and ingredient['unittype'] == 'count' and ingredient['notation'] != '':
            ingredient['quantity'] = ""
    cur.execute("""
        select s.description
           from step s
           inner join recipe r on s.recipeId = r.id
           where r.id = %s
           order by s.displayorder;
    """, (id,))
    steps = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('recipe.html', recipe=recipe, ingredients=ingredients, steps=steps)

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM recipe;")
    recipes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', recipes=recipes)

