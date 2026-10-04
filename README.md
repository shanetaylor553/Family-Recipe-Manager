# Family Recipes V 1.0
#### Video Demo: https://youtu.be/AEliUSFeaAK?is+IQuqs4dzoXKvzedf
#### Description: 
Family Recipes is a small cookbook web app for collecting and browsing recipes in one dedicated place. It is built with Python and Flask, uses SQLite to store its data, and renders pages with Jinja templates and shared CSS.

## Why I Built It

I built this project to have a dedicated family recipe cookbook app: one place to keep the dishes my family makes, organize them by category, and find them again without searching through loose notes or messages. The goal is to make it easier to preserve recipes and the stories and routines around them.

## What It Does

- Creates user accounts, logs users in and out, and stores password hashes rather than plain-text passwords.
- Lists recipes and categories stored in SQLite.
- Searches recipes by recipe name, category, description, or ingredient.
- Groups recipes by their assigned category.
- Shows recipe descriptions, preparation and cooking times, servings, ingredient quantities, and numbered instructions.
- Allows recipe records to be added, edited, and deleted.
- Provides a responsive interface for desktop and mobile screens.

The three starter recipes in the database are Fluffy Buttermilk Pancakes, Chicken Noodle Soup, and Black Bean and Sweet Potato Tacos. They each include ingredients and instructions. The current Add Recipe and Edit Recipe forms handle the recipe name, category, and description; editing ingredient lists and instructions through those forms is not implemented yet.

## How It Works

- `app.py` defines the Flask routes, validates form submissions, performs database queries, and renders templates.
- `database.py` creates the SQLite tables and opens database connections. The database file is `family_recipes.db`.
- `templates/` contains the HTML/Jinja pages. `base.html` provides the shared navigation and page structure.
- `static/styles.css` contains the shared responsive styles.
- SQLite stores users, recipes, categories, ingredients, recipe-to-ingredient quantities, and ordered recipe steps.

When the app starts, `init_db()` creates any missing tables and adds recipe timing/serving columns to an older recipes table when needed. Existing account and category records are kept in the database.

## Run the App

Open a terminal in the project folder:

```sh
cd /path/to/family-recipes
```

Create and activate a virtual environment if the project does not already have one:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install Flask into that environment if needed:

```sh
python -m pip install Flask
```

Start the development server:

```sh
python app.py
```

If you do not want to activate the environment, run it directly from the project folder:

```sh
.venv/bin/python app.py
```

Open the address printed by Flask, usually `http://127.0.0.1:5000/`. If port 5000 is already being used, stop the other server or start this one on another port:

```sh
.venv/bin/python -m flask --app app run --port 5001 --debug
```

Select `.venv/bin/python` as the Python interpreter in VS Code so the editor and terminal use the environment where Flask is installed.

## Debugging Challenges

Several issues came from small mismatches between tools and assumptions:

- Flask was installed in the project virtual environment, but VS Code or the terminal sometimes launched a different Python interpreter. Selecting `.venv/bin/python` fixed the import mismatch.
- Some templates used Django template syntax such as `{% url ... %}` and `request.GET`. Flask uses Jinja's `url_for(...)` and Flask's `request.args` instead.
- Flask only finds rendered page templates inside `templates/`; static files such as CSS belong in `static/`.
- The home page referred to `current_user` even though Flask-Login was not configured. Removing that undefined reference fixed its server error.
- Recipe/category bugs were caused by mixing hard-coded sample data with database-backed routes and by recipes being saved with the same category ID. Using the database assignment for category filtering and requiring a deliberate category selection made the results consistent.
- SQLite schema changes and SQL syntax needed to match the SQLite version and existing database. Small route and database checks helped catch syntax errors, template errors, missing records, and category mismatches before relying on the browser.

## AI Assistance Disclosure

GitHub Copilot, an AI coding assistant, was used during development to help write and review application code, troubleshoot errors, draft this README, and prepare the three starter recipes and their instructions. The project owner reviewed the changes and ran application checks. AI-generated recipe details are starter content and should be checked for personal preferences, dietary needs, and food safety before use. No external sources are claimed for the recipe text.

## Development Note

This is a learning and development project. Before deploying it publicly, replace the development Flask secret key with a private environment variable, add production security protections (including CSRF protection), and use a production WSGI server instead of Flask's development server.
