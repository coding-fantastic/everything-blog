from flask import Flask , render_template, session , flash ,redirect, url_for , session, logging, request
from data import Articles
from flask_mysqldb import MySQL 
from wtforms import Form, StringField , TextAreaField, PasswordField , validators
from passlib.hash import sha256_crypt

app = Flask(__name__)

# config MySQL 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MySQL 
mysql = MySQL(app)

Articles = Articles()

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
    return render_template('articles.html', articles = Articles)

# single article 
@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id=id)

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

# logout 
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out' , 'success')
    return redirect(url_for('login'))

# dashboard  
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)