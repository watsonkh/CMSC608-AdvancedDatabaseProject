from flask import Flask, render_template
from markupsafe import escape
from flask import request


app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/recipe_search', methods=['GET', 'POST'])
def recipe_search():
    if request.method == 'POST':
        query = request.form.get('search_query')

        # just re-renders the query, will need to get from db
        return render_template('recipe_search.html', search_results=query)

        # should do something like:
        # conn = get_db_connection()
        # cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # cur.execute(f"SELECT * FROM recipe WHERE {query} in ingredients or {query} in {name};") # vulnerable to sql injection
        # recipes = cur.fetchall()
        # cur.close()
        # conn.close()
        # return render_template('recipe_search.html', search_results=recipes)
    return render_template('recipe_search.html', search_results=[])


# @app.route('/recipe_search/q=<string:query>')
# def recipe_search(query):
#     return render_template('recipe_search.html', recipe_id=query)


# TESTING ONLY
@app.route('/base')
def base():
    return render_template('base.html')

# @app.route("/<name>")
# def hello(name):
#     return f"Hello, {escape(name)}!"