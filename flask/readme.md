## Getting Started

In order to locally run Flask on your machine, follows these installation instructions:

* https://flask.palletsprojects.com/en/stable/installation/

Since the `app.py` script relies on using the Python library `psycopg2` to connect to your locally running Postgres DB, you will also have to

1. Install psycopg2 and python-dotenv to your virtual environment:
    * `pip install psycopg2-binary python-dotenv`
2. Ensure your PostgresDB is running, and initialize the DB using the following .sql statement order:
    * `tables.sql`
    * `data.sql`
    * Run `tx.py`, then
        * `output.sql`
3. Add a .env file to the flask folder for the `app.py` to read so it can connect to your Postgres DB. I use the following .env format:

HOST=localhost

DATABASE=dbname

USER=username

PASSWORD=password

If I haven't missed anything, you should be able to initialize the Flask instance now. CD to the flask folder and run
 
* `flask --app app run` OR
* `flask --app app run --debug` if you want Flask to output debug logs while you're making changes to the website. 
