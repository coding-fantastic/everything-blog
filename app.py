from flask import Flask , render_template, session , flash ,redirect, url_for , session, logging, request
# from data import Articles
from flask_mysqldb import MySQL 
from wtforms import Form, StringField , TextAreaField, PasswordField , validators
from passlib.hash import sha256_crypt
from functools  import wraps

app = Flask(__name__)

# config MySQL 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MySQL 
mysql = MySQL(app)

# Articles = Articles()

# index  
@app.route('/')
def index():
    return render_template('home.html')

# about 
@app.route('/about')
def about():
    return render_template('about.html')

# articles 
@app.route('/articles')
def articles():
    # create cursor  
    cur=mysql.connection.cursor()
    
    # get articles 
    result = cur.execute("SELECT * FROM articles")

    # fetch everything in dictonary form 
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles = articles)
    else:
        msg = 'No Articles was found '
        return render_template('articles.html', msg = msg)
    
    # close connection 
    cur.close()

# single article 
@app.route('/article/<string:id>/')
def article(id):
    # create cursor  
    cur=mysql.connection.cursor()
    
    # get articles 
    result = cur.execute("SELECT * FROM articles where id = %s", [id] )

    # fetch everything in dictonary form 
    article = cur.fetchone()
    return render_template('article.html', article=article)

# register form class   
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('username', [validators.Length(min=4, max=25)])
    email = StringField('email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
        ])
    confirm = PasswordField('Confirm Password')

# user register 
@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # creat cursor 
        cur = mysql.connection.cursor()
        
        # execute query 
        cur.execute("INSERT into users(name, email, username ,password) VALUES (%s, %s ,%s, %s) ", (name , email , username , password))

        # commit to db 
        mysql.connection.commit() 

        # close connection 
        cur.close()

        flash('You are now registered and can login', 'success')
         
        return redirect(url_for('login'))
    return render_template('register.html', form = form)

# user login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get username and passsword from form posted
        username = request.form['username']
        password_candidate = request.form['password']

        # create a cursor 
        cur = mysql.connection.cursor()

        # get user by username 
        result = cur.execute("SELECT * FROM users WHERE username = %s ", [username])

        # check if the is any row found 
        if result > 0:
            # get stored hash  
            data = cur.fetchone()
            password = data['password']

            # compare passwords 
            if sha256_crypt.verify(password_candidate, password):
                # app.logger.info('PASSWORD MATCHED')
                session['logged_in'] = True 
                session['username'] = username 

                flash('You are now logged in' , 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'invalid login'
                return render_template('login.html', error=error)
            # close connection 
            cur.close()
        else:
            error = 'username not found'
            return render_template('login.html', error = error)

    return render_template('login.html')

# check if user login 
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs ):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized , Please login ', 'danger')
            return redirect(url_for('login'))
    return wrap

# logout 
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out' , 'success')
    return redirect(url_for('login'))

# dashboard  
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor  
    cur=mysql.connection.cursor()
    
    # get articles 
    result = cur.execute("SELECT * FROM articles")

    # fetch everything in dictonary form 
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles = articles)
    else:
        msg = 'No Articles was found '
        return render_template('dashboard.html', msg = msg)
    
    # close connection 
    cur.close()

    return render_template('dashboard.html')

# article form class   
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = StringField('Body', [validators.Length(min=30)])
    
# add article route
@app.route('/add_article', methods = ['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and  form.validate():
        title = form.title.data
        body = form.body.data 

        # create cursor 
        cur = mysql.connection.cursor()

        # execute
        cur.execute("INSERT INTO  articles (title, body , author ) VALUES(%s, %s , %s)", (title , body , session['username']))

        # commit to db    
        mysql.connection.commit()

        # close connection  
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form = form)

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)