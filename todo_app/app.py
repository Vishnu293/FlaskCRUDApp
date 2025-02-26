from flask import Flask, request, jsonify, session, render_template, redirect, url_for, flash
from sqlalchemy import URL
from models import User, Task, db, convert_to_ist
from support import get_config_details
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(get_config_details("app_name"),
    template_folder="templates",
    static_folder="static")
CORS(app, supports_credentials=True)

app.config['CORS_SUPPORTS_CREDENTIALS'] = 'true'
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SQLALCHEMY_DATABASE_URI'] = URL.create("mysql+pymysql", get_config_details('username'), get_config_details('password'), host=get_config_details('hostname'), port=get_config_details('port'), database=get_config_details('database'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = get_config_details('secret_key')

db.init_app(app)

with app.app_context():
    db.create_all()

def is_authenticated():
    return 'user_id' in session

@app.route('/', methods=["GET"])
def home():
    if is_authenticated():
        page = request.args.get('page', 1, type=int)

        tasks = Task.query.filter_by(user_id=session['user_id']) \
                .order_by(Task.completed, Task.created_at.desc()) \
                .paginate(page=page, per_page=10, error_out=False)

        for task in tasks.items:
            ist_time = convert_to_ist(task.created_at) 
            
            task.created_date = ist_time.strftime('%d-%m-%Y')
            task.created_time = ist_time.strftime('%I:%M %p')

        return render_template(
            'index.html', 
            tasks=tasks.items, 
            current_page=tasks.page, 
            next_page=tasks.next_num,
            prev_page=tasks.prev_num, 
            has_next=tasks.has_next, 
            has_prev=tasks.has_prev
        )

    return render_template('index.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('signup.html')
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash("Missing required fields", "warning")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("User registered successfully. Please log in.", "success")
        return redirect(url_for('login'))
    
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('register'))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    try:
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Missing email or password", "warning")
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful", "success")
            return redirect('/')
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))

    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('login'))

@app.route('/logout', methods=["GET", "POST"])
def logout():
    try:
        session.pop('user_id', None)
        session.pop('username', None) 
        flash("Logout successful", "success")
        return redirect(url_for('home')) 
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('home'))

@app.route('/protected', methods=["GET"])
def protected():
    if is_authenticated():
        return jsonify({"message": "You are logged in"}), 200
    else:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/dashboard', methods=["GET"])
def dashboard():
    if is_authenticated():
        return render_template('dashboard.html'), 200
    return redirect(url_for('login'))

@app.route('/add', methods=["POST"])
def add_task():
    if not is_authenticated():
        flash("Please log in to add tasks.", "danger")
        return redirect(url_for('login'))
    
    try:
        task_name = request.form.get('task')
        if not task_name:
            flash("Task content cannot be empty", "warning")
            return redirect('/')
        
        new_task = Task(name=task_name, user_id=session['user_id'])
        db.session.add(new_task)
        db.session.commit()
        
        flash("Task added successfully", "success")
        return redirect('/')
    except Exception as e:
        flash(str(e), "danger")
        return redirect('/')

@app.route('/complete/<int:task_id>', methods=["POST"])
def complete_task(task_id):
    if not is_authenticated():
        flash("Please log in to mark tasks as complete.", "danger")
        return redirect(url_for('login'))
    
    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        task.completed = True
        db.session.commit()
        flash("Task marked as complete", "success")
    else:
        flash("You are not authorized to complete this task.", "danger")
    
    return redirect('/')

@app.route('/delete/<int:task_id>', methods=["POST"])
def delete_task(task_id):
    if not is_authenticated():
        flash("Please log in to delete tasks.", "danger")
        return redirect(url_for('login'))
    
    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted", "success")
    else:
        flash("You are not authorized to delete this task.", "danger")
    
    return redirect('/')

if __name__ == '__main__':
    app.run(host=get_config_details("app_hostname"), port=get_config_details("app_port"))

