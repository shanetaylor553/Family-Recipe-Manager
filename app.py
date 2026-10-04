# imports
try:
    from flask import Flask, redirect, render_template, request, session, url_for
    from werkzeug.security import check_password_hash, generate_password_hash
    from database import init_db, get_db_connection
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        "Flask is required to run this application. Install it with: pip install Flask"
    ) from error

app = Flask(__name__)

init_db()  # Initialize the database when the app starts

app.secret_key = 'family-recipes-development-key'

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    if user_id is None:
        return {'username': None}
    db = get_db_connection()
    user = db.execute('SELECT name FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    return {'username': user['name'] if user else None}

@app.route('/')
#home page function
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        if email == '':
            email = None  # Set email to None if it's an empty string
        db = get_db_connection()
        user = db.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if not username and not email:
            error = 'Username or email is required.'
        elif not password:
            error = 'Password is required.'
        elif user is not None:
            error = 'That username or email is already registered.'
        else:
            cursor = db.execute('INSERT INTO users (username, password_hash, name, email) VALUES (?, ?, ?, ?)',
                       (username, generate_password_hash(password), name, email))
            db.commit()
            session['user_id'] = cursor.lastrowid
            return redirect(url_for('home'))
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        db = get_db_connection()
        user = db.execute('SELECT * FROM users WHERE username = ? OR email = ?', (login, login)).fetchone()
        if user is None or not check_password_hash(user['password_hash'], password):
            error = 'Invalid username or password.'
        else:
            session['user_id'] = user['id']
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/recipes')
def recipes():
    search_term = request.args.get('q', '').strip()
    db = get_db_connection()
    query = '''SELECT recipes.id, recipes.name, categories.name AS category, recipes.description,
                      recipes.prep_time_minutes, recipes.cook_time_minutes, recipes.servings
           FROM recipes
           JOIN categories ON recipes.category_id = categories.id'''
    parameters = ()
    if search_term:
        query += '''
           WHERE recipes.name LIKE ? OR categories.name LIKE ? OR recipes.description LIKE ?
              OR EXISTS (
                  SELECT 1 FROM recipe_ingredients
                  JOIN ingredients ON ingredients.id = recipe_ingredients.ingredient_id
                  WHERE recipe_ingredients.recipe_id = recipes.id AND ingredients.name LIKE ?
              )'''
        wildcard_term = f'%{search_term}%'
        parameters = (wildcard_term,) * 4
    query += ' ORDER BY recipes.name'
    recipes = db.execute(query, parameters).fetchall()
    db.close()
    return render_template('recipes.html', recipes=recipes, search_term=search_term)

@app.route('/recipes/add', methods=['GET', 'POST'])
def add_recipe():
    db = get_db_connection()
    categories = db.execute('SELECT id, name FROM categories ORDER BY name').fetchall()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', '').strip()
        description = request.form.get('description', '').strip()
        if not name or not category_id:
            error = 'All fields are required.'
        elif db.execute(
            'SELECT 1 FROM categories WHERE id = ?', (category_id,)
        ).fetchone() is None:
            error = 'Choose a valid category.'
        else:
            db.execute(
                'INSERT INTO recipes (name, category_id, description) VALUES (?, ?, ?)',
                (name, category_id, description),
            )
            db.commit()
            db.close()
            return redirect(url_for('recipes'))
        db.close()
        return render_template('add_recipe.html', categories=categories, error=error)
    db.close()
    return render_template('add_recipe.html', categories=categories)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/categories')
def categories():
    search_term = request.args.get('q', '').strip()
    db = get_db_connection()
    matching_categories = db.execute(
        'SELECT id, name FROM categories ORDER BY name'
    ).fetchall()
    db.close()
    if search_term:
        search_text = search_term.lower()
        matching_categories = [
            category for category in matching_categories
            if search_text in category['name'].lower()
        ]
    return render_template(
        'categories.html',
        categories=matching_categories,
        search_term=search_term,
    )

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    db = get_db_connection()
    recipe = db.execute(
        '''SELECT recipes.id, recipes.name, categories.name AS category, recipes.description,
                  recipes.prep_time_minutes, recipes.cook_time_minutes, recipes.servings
           FROM recipes
           JOIN categories ON recipes.category_id = categories.id
           WHERE recipes.id = ?''',
        (recipe_id,),
    ).fetchone()
    ingredients = []
    steps = []
    if recipe is not None:
        ingredients = db.execute(
            '''SELECT ingredients.name, recipe_ingredients.quantity
               FROM recipe_ingredients
               JOIN ingredients ON ingredients.id = recipe_ingredients.ingredient_id
               WHERE recipe_ingredients.recipe_id = ?
               ORDER BY ingredients.name''',
            (recipe_id,),
        ).fetchall()
        steps = db.execute(
            'SELECT step_number, description FROM steps WHERE recipe_id = ? ORDER BY step_number',
            (recipe_id,),
        ).fetchall()
    db.close()
    if recipe is None:
        return 'Recipe not found', 404
    return render_template(
        'recipe_detail.html', recipe=recipe, ingredients=ingredients, steps=steps
    )

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    db = get_db_connection()
    categories = db.execute('SELECT id, name FROM categories ORDER BY name').fetchall()
    recipe = db.execute(
        'SELECT id, name, category_id, description FROM recipes WHERE id = ?',
        (recipe_id,),
    ).fetchone()
    if recipe is None:
        db.close()
        return 'Recipe not found', 404

    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category_id']
        description = request.form['description']

        if not name or not category_id:
            error = 'Name and category are required.'
        elif db.execute(
            'SELECT 1 FROM categories WHERE id = ?', (category_id,)
        ).fetchone() is None:
            error = 'Choose a valid category.'
        else:
            db.execute(
                'UPDATE recipes SET name = ?, category_id = ?, description = ? WHERE id = ?',
                (name, category_id, description, recipe_id)
            )
            db.commit()
            db.close()
            return redirect(url_for('recipe_detail', recipe_id=recipe_id))
        db.close()
        return render_template('edit_recipe.html', recipe=recipe, error=error, categories=categories)

    db.close()
    return render_template('edit_recipe.html', recipe=recipe, categories=categories)

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    db = get_db_connection()
    db.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
    db.commit()
    db.close()
    return redirect(url_for('recipes'))

@app.route('/category/<int:category_id>')
def category_recipes(category_id):
    db = get_db_connection()
    category = db.execute(
        'SELECT id, name FROM categories WHERE id = ?',
        (category_id,),
    ).fetchone()
    if category is None:
        db.close()
        return 'Category not found', 404
    category_recipes = db.execute(
        '''SELECT recipes.id, recipes.name, categories.name AS category, recipes.description
           FROM recipes
           JOIN categories ON recipes.category_id = categories.id
           WHERE recipes.category_id = ?
           ORDER BY recipes.name''',
        (category_id,),
    ).fetchall()
    db.close()
    return render_template(
        'recipes.html',
        recipes=category_recipes,
        search_term='',
        category_name=category['name'],
    )

if __name__ == '__main__':
    app.run(debug=True)