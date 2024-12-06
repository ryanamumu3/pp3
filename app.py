from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração do Flask e do banco de dados
project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "bookdatabase.db"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.secret_key = os.urandom(24)  # Necessário para sessões
db = SQLAlchemy(app)

# Modelos de banco de dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

class Book(db.Model):
    title = db.Column(db.String(80), unique=True, nullable=False, primary_key=True)
    description = db.Column(db.Text, nullable=True)  # Nova coluna para descrição
    rating = db.Column(db.Float, nullable=True)      # Nova coluna para nota (float)

    def __repr__(self):
        return f"<Book {self.title}>"

with app.app_context():
    db.create_all()  # Criação das tabelas no banco de dados

# Rota inicial (redirecionar para cadastro ou lista de livros)
@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        return redirect("/register")  # Redireciona para a tela de cadastro se não estiver logado

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        rating = request.form.get("rating")

        try:
            book = Book(title=title, description=description, rating=float(rating))
            db.session.add(book)
            db.session.commit()
            flash("Livro adicionado com sucesso!", "success")
        except Exception as e:
            flash("Falha ao adicionar livro", "danger")
            print("Falha ao adicionar livro:", e)

    books = Book.query.all()
    return render_template("index.html", books=books)

# Rota de cadastro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Verifica se o usuário ou email já existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Nome de usuário já existe. Escolha outro.", "danger")
            return redirect("/register")
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("E-mail já cadastrado. Use outro.", "danger")
            return redirect("/register")
        
        # Criptografando a senha
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Usuário cadastrado com sucesso!", "success")
        return redirect("/login")
    
    return render_template("register.html")

# Rota de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login realizado com sucesso!", "success")
            return redirect("/")
        else:
            flash("Credenciais inválidas. Tente novamente.", "danger")
    
    return render_template("login.html")

# Rota de logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu com sucesso!", "success")
    return redirect("/login")

# Rota de atualização de livro
@app.route("/update", methods=["POST"])
def update():
    try:
        newtitle = request.form.get("newtitle")
        oldtitle = request.form.get("oldtitle")
        book = Book.query.filter_by(title=oldtitle).first()
        if book:
            book.title = newtitle
            db.session.commit()
            flash("Título do livro atualizado com sucesso!", "success")
        else:
            flash("Livro não encontrado.", "danger")
    except Exception as e:
        flash("Falha ao atualizar título do livro", "danger")
        print("Falha ao atualizar título do livro:", e)
    return redirect("/")

# Rota de exclusão de livro
@app.route("/delete", methods=["POST"])
def delete():
    title = request.form.get("title")
    book = Book.query.filter_by(title=title).first()
    if book:
        db.session.delete(book)
        db.session.commit()
        flash("Livro excluído com sucesso!", "success")
    else:
        flash("Livro não encontrado.", "danger")
    return redirect("/")

# Rota para ver detalhes do livro
@app.route("/jogo/<title>", methods=["GET"])
def jogo(title):
    book = Book.query.filter_by(title=title).first()  
    if book:
        return render_template("jogo.html", book=book)
    else:
        return "Livro não encontrado", 404

# Inicializando o servidor
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
