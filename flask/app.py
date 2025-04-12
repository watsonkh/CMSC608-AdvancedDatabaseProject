import os
import imghdr
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image
from embeddings import init_CLIP, create_embedding
from queries import image_similarity_query, recipe_steps_query

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
    cur.execute(f"SELECT * FROM recipe WHERE id = %s ;", (id,))
    recipe = cur.fetchone()
    cur.execute(f"SELECT * FROM step WHERE recipeId = %s ORDER BY displayorder ;", (id,))
    steps = cur.fetchall()
    cur.execute(recipe_steps_query, (id,))
    ingredients = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('recipe.html', recipe=recipe, steps=steps, ingredients=ingredients)

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM recipe ORDER BY id ;")
    recipes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', recipes=recipes)


@app.route('/admin')
def admin_panel():
    return render_template('admin.html')
@app.route('/admin/recipe')
def admin_recipe_list():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM recipe ORDER BY id ;")
    recipes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_recipe_list.html', recipes=recipes)

@app.route('/admin/recipe/add', methods=['GET', 'POST'])
def admin_recipe_add():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        servings = request.form['servings']
        mainimage = request.form['mainimage']

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(
                "INSERT INTO recipe (name, description, servings, mainimage) VALUES (%s, %s, %s, %s);",
                (name, description, servings, mainimage)
            )
            conn.commit()
            flash('Recipe added successfully!', 'success')
            return redirect(url_for('admin_recipe_list')) # Redirect to recipe list
        except Exception as e:
            conn.rollback()
            flash(f'Error adding recipe: {e}', 'error')
        finally:
            cur.close()
            conn.close()
    return render_template('admin_recipe_add.html')

@app.route('/admin/recipe/edit/<int:id>', methods=['GET', 'POST'])
def admin_recipe_edit(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    recipe = None
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        servings = request.form['servings']
        mainimage = request.form['mainimage']

        try:
            cur.execute(
                "UPDATE recipe SET name=%s, description=%s, servings=%s, mainimage=%s WHERE id=%s;",
                (name, description, servings, mainimage, id)
            )
            conn.commit()
            flash('Recipe updated successfully!', 'success')
            return redirect(url_for('admin_recipe_list'))
        except Exception as e:
            conn.rollback()
            flash(f'Error updating recipe: {e}', 'error')
        finally:
            cur.close()
            conn.close()
    else: # GET request to display edit form
        cur.execute("SELECT * FROM recipe WHERE id = %s;", (id,))
        recipe = cur.fetchone()
        cur.close()
        conn.close()
        if recipe is None:
            flash('Recipe not found', 'error')
            return redirect(url_for('admin_recipe_list'))

    return render_template('admin_recipe_edit.html', recipe=recipe)

@app.route('/admin/recipe/delete/<int:id>')
def admin_recipe_delete(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("DELETE FROM recipe WHERE id = %s;", (id,))
        conn.commit()
        flash('Recipe deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting recipe: {e}', 'error')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_recipe_list'))