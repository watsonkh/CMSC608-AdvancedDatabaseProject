import os
import imghdr
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image
from embeddings import init_CLIP, create_embedding, create_text_embedding
import queries as query

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
TABLES_TO_MANAGE = ['recipe', 'ingredient', 'unit', 'step']
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
                cur.execute(query.image_similarity_query, (img_embedding, img_embedding, img_embedding))
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
    cur.execute(query.recipe_ingredients_query, (id,))
    ingredients = cur.fetchall()
    for ingredient in ingredients:
        if ingredient['denominator'] is not None:
            whole = ingredient['quantity'] // ingredient['denominator']
            if whole > 0:
                ingredient['quantity'] = f"{whole} {ingredient['quantity'] % ingredient['denominator']}/{ingredient['denominator']}"
            else:
                ingredient['quantity'] = f"{ingredient['quantity']} / {ingredient['denominator']}"
        elif ingredient['quantity'] == 1 and ingredient['unittype'] == 'use' and ingredient['notation'] == '':
            ingredient['quantity'] = ""
    cur.execute(query.recipe_steps_query, (id,))
    steps = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('recipe.html', recipe=recipe, ingredients=ingredients, steps=steps)

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
    return render_template('admin.html', tables=TABLES_TO_MANAGE)

@app.route('/admin/<table_name>')
def admin_list(table_name):
    if table_name not in TABLES_TO_MANAGE:
        flash('Invalid table name', 'error')
        return redirect(url_for('admin_panel'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Get column names dynamically
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position;")
        columns_result = cur.fetchall()
        column_names = [col['column_name'] for col in columns_result]
        if 'recipeid' in column_names:
            cur.execute(f"SELECT * FROM {table_name} ORDER BY recipeid, id;")
        else:
        # Fetch data from the table
            cur.execute(f"SELECT * FROM {table_name} ORDER BY id;") # No ordering for generic list for now, can add later
        data = cur.fetchall()
    except Exception as e:
        cur.close()
        conn.close()
        flash(f'Error fetching data for table {table_name}: {e}', 'error')
        return redirect(url_for('admin_panel'))
    finally:
        cur.close()
        conn.close()

    return render_template('admin_list.html', table_name=table_name, columns=column_names, data=data)

@app.route('/admin/<table_name>/add', methods=['GET', 'POST'])
def admin_add(table_name):
    if table_name not in TABLES_TO_MANAGE:
        flash('Invalid table name', 'error')
        return redirect(url_for('admin_panel'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        # Get column names for form generation (excluding serial/id columns if needed)
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position;")
        columns_info_result = cur.fetchall()
        columns_info = [{'name': col['column_name'], 'type': col['data_type']} for col in columns_info_result] # Get column name and type

        if request.method == 'POST':
            column_names = [col_info['name'] for col_info in columns_info if col_info['name'] not in ['id']] # Exclude 'id' for INSERT
            values = [request.form.get(col) for col in column_names] # Get values from form

            placeholders = ', '.join(['%s'] * len(column_names))
            columns_str = ', '.join(column_names)
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"

            try:
                cur.execute(insert_query, tuple(values))
                conn.commit()
                flash(f'{table_name.capitalize()} added successfully!', 'success')
                return redirect(url_for('admin_list', table_name=table_name))
            except Exception as e:
                conn.rollback()
                flash(f'Error adding {table_name.capitalize()}: {e}', 'error')

    except Exception as e:
        cur.close()
        conn.close()
        flash(f'Error preparing add form for {table_name.capitalize()}: {e}', 'error')
        return redirect(url_for('admin_panel'))
    finally:
        if request.method == 'GET': # Only close connection if it's a GET request, POST path handles closing in its own scope
            cur.close()
            conn.close()


    return render_template('admin_add.html', table_name=table_name, columns_info=columns_info)

@app.route('/admin/<table_name>/edit/<id>', methods=['GET', 'POST'])
def admin_edit(table_name, id):
    if table_name not in TABLES_TO_MANAGE:
        flash('Invalid table name', 'error')
        return redirect(url_for('admin_panel'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data_item = None

    try:
        # Get column names and data types for form generation
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position;")
        columns_info_result = cur.fetchall()
        columns_info = [{'name': col['column_name'], 'type': col['data_type']} for col in columns_info_result]

        if request.method == 'POST':
            set_clauses = []
            update_values = []
            for col_info in columns_info:
                col_name = col_info['name']
                if col_name != 'id': # Don't update ID column
                    set_clauses.append(f"{col_name} = %s")
                    update_values.append(request.form.get(col_name))

            update_values.append(id) # Add ID for WHERE clause
            set_clause_str = ', '.join(set_clauses)
            update_query = f"UPDATE {table_name} SET {set_clause_str} WHERE id = %s;"

            try:
                cur.execute(update_query, tuple(update_values))
                conn.commit()
                flash(f'{table_name.capitalize()} updated successfully!', 'success')
                return redirect(url_for('admin_list', table_name=table_name))
            except Exception as e:
                conn.rollback()
                flash(f'Error updating {table_name.capitalize()}: {e}', 'error')

        else: # GET request to display edit form
            cur.execute(f"SELECT * FROM {table_name} WHERE id = %s;", (id,))
            data_item = cur.fetchone()
            if data_item is None:
                flash(f'{table_name.capitalize()} not found', 'error')
                return redirect(url_for('admin_list', table_name=table_name))

    except Exception as e:
        cur.close()
        conn.close()
        flash(f'Error preparing edit form for {table_name.capitalize()}: {e}', 'error')
        return redirect(url_for('admin_list', table_name=table_name))
    finally:
        if request.method == 'GET': # Only close connection if GET, POST path handles closing in its own scope
            cur.close()
            conn.close()


    return render_template('admin_edit.html', table_name=table_name, columns_info=columns_info, data_item=data_item, item_id=id)

@app.route('/admin/<table_name>/delete/<id>')
def admin_delete(table_name, id):
    if table_name not in TABLES_TO_MANAGE:
        flash('Invalid table name', 'error')
        return redirect(url_for('admin_panel'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(f"DELETE FROM {table_name} WHERE id = %s;", (id,))
        conn.commit()
        flash(f'{table_name.capitalize()} deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting {table_name.capitalize()}: {e}', 'error')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_list', table_name=table_name))



@app.route('/recipe_search', methods=['GET', 'POST'])
def recipe_search():
    if request.method == 'POST':
        query = request.form.get('search_query')

        # Fuzzy search:
        embedding = create_text_embedding([query])[0].astype(float).tolist()
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(f"SELECT id, name, mainimage, description from recipe INNER JOIN recipe_embeddings on recipe.id=recipe_embeddings.recipeid ORDER BY description_embedding <=> %s::vector DESC LIMIT 10", (embedding,))
        recipes = cur.fetchall()
        cur.close()
        conn.close()
        if len(recipes) > 0:
            return render_template('recipe_search.html', search_results=recipes, query=query, text="")
        else:
            return render_template('recipe_search.html', search_results=recipes, query=query, text="No results found")
        

        # Exact search:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(f"SELECT * from public.recipe WHERE LOWER(name) LIKE '%%' || LOWER(%s) || '%%' OR LOWER(description) LIKE '%%' || LOWER(%s) || '%%' ;", (query, query))
        recipes = cur.fetchall()
        cur.close()
        conn.close()
        if len(recipes) > 0:
            return render_template('recipe_search.html', search_results=recipes, query=query, text="")
        else:
            return render_template('recipe_search.html', search_results=recipes, query=query, text="No results found")
    return render_template('recipe_search.html', search_results=[], query='', text="")




@app.route('/advanced_search', methods=['GET', 'POST'])
def advanced_search():
    if request.method == 'POST':
        query_name = request.form.get('query_name')
        query_ingredients = request.form.get('query_ingredients')
        query_steps = request.form.get('query_steps')
        query_description = request.form.get('query_description')

        # Exact search:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(f"SELECT DISTINCT r.id, r.name, r.mainimage, r.description from recipe r inner join step s on r.id = s.recipeid inner join recipe_ingredient ri on ri.recipeid = r.id inner join ingredient i on i.id = ri.ingredientid WHERE LOWER(r.name) LIKE '%%' || LOWER(%s) || '%%' AND LOWER(r.description) LIKE '%%' || LOWER(%s) || '%%' AND LOWER(s.description) LIKE '%%' || LOWER(%s) || '%%' AND LOWER(i.name) LIKE '%%' || LOWER(%s) || '%%';", (query_name, query_description, query_steps, query_ingredients))
        recipes = cur.fetchall()
        cur.close()
        conn.close()
        if len(recipes) > 0:
            return render_template('advanced_search.html', search_results=recipes, query=query, text="")
        else:
            return render_template('advanced_search.html', search_results=recipes, query=query, text="No results found")
    return render_template('advanced_search.html', search_results=[], query='', text="")