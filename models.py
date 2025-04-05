from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    genero = db.Column(db.String(50), nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    token_balance = db.Column(db.Integer, default=0)
    profile_pic = db.Column(db.String(100), nullable=True, default='default_profile.jpg')  # Nueva columna
    whatsapp = db.Column(db.String(20), nullable=True)  # Nuevo campo para WhatsApp
    carrusel_imagenes = db.Column(db.JSON, nullable=True)  # Nuevo campo para las imágenes del carrusel
# Para transacciones

    
    # Relaciones (usando back_populates)
    galerias = db.relationship('Galeria', back_populates='usuario', lazy=True, cascade='all, delete-orphan')
    posts = db.relationship('Post', back_populates='usuario', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Usuario {self.username}>'


class Galeria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    imagen_portada = db.Column(db.String(100), nullable=False)  # Imagen principal del pack
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    
    # Relación con el usuario
    usuario = db.relationship('Usuario', back_populates='galerias')
    
    # Relación con las imágenes del pack
    imagenes = db.relationship('GalleryImage', back_populates='galeria', lazy=True, cascade='all, delete-orphan')


class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imagen = db.Column(db.String(100), nullable=False)  # Ruta de cada imagen en el pack
    galeria_id = db.Column(db.Integer, db.ForeignKey('galeria.id', ondelete='CASCADE'), nullable=False)
    
    # Relación con la galería
    galeria = db.relationship('Galeria', back_populates='imagenes')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Enum('publicacion', 'anuncio', name='post_types'), nullable=False)
    contenido = db.Column(db.Text)  # Opcional para anuncios
    imagen = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    ciudad = db.Column(db.String(150), nullable=False)
    
 # Relación con el usuario
    usuario = db.relationship('Usuario', back_populates='posts')

    __mapper_args__ = {
        'polymorphic_on': tipo,  # Columna que define el tipo de post
        'with_polymorphic': '*'  # Cargar todos los tipos de posts
    }

class Publicacion(Post):
    __mapper_args__ = {
        'polymorphic_identity': 'publicacion'  # Identificador único para publicaciones
    }

class Anuncio(Post):
    __mapper_args__ = {
        'polymorphic_identity': 'anuncio'  # Identificador único para anuncios
    }

class costos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    publicar = db.Column(db.Integer, nullable=False)
