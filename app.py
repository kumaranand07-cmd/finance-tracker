from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    source = db.Column(db.String(100))
    date = db.Column(db.String(20))

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    category = db.Column(db.String(100))
    date = db.Column(db.String(20))

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    uid = session['user_id']
    start_date = None
    end_date = None

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

    incomes_query = Income.query.filter_by(user_id=uid)
    expenses_query = Expense.query.filter_by(user_id=uid)

    if start_date and end_date:
        incomes_query = incomes_query.filter(Income.date.between(start_date, end_date))
        expenses_query = expenses_query.filter(Expense.date.between(start_date, end_date))

    incomes = incomes_query.order_by(Income.date.desc()).all()
    expenses = expenses_query.order_by(Expense.date.desc()).all()

    total_income = sum([i.amount for i in incomes])
    total_expense = sum([e.amount for e in expenses])
    balance = total_income - total_expense

    from collections import defaultdict
    category_totals = defaultdict(float)
    for exp in expenses:
        category_totals[exp.category] += exp.amount

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())

    return render_template(
        'dashboard.html',
        name=session['user_name'],
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        incomes=incomes,
        expenses=expenses,
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        amounts=amounts
    )

@app.route('/add_income', methods=['GET', 'POST'])
def add_income():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        amount = float(request.form['amount'])
        source = request.form['source']
        date = request.form['date']
        income = Income(user_id=session['user_id'], amount=amount, source=source, date=date)
        db.session.add(income)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_income.html')

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']
        expense = Expense(user_id=session['user_id'], amount=amount, category=category, date=date)
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_expense.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
