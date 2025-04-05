from flask_login import LoginManager
from flask import Flask
from database import db
from routes import init_routes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db.init_app(app)

# Configurar Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Cargar rutas
init_routes(app, login_manager)

# Crear tablas
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=8000)