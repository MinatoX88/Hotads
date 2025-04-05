from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, Email
from wtforms import TextAreaField, FileField, SubmitField  # Importa TextAreaField

class LoginForm(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Iniciar Sesión")

class RegistroForm(FlaskForm):
    username = StringField("Nombre de Usuario", validators=[DataRequired(), Length(min=3, max=20)])
    edad = IntegerField("Edad", validators=[DataRequired(), NumberRange(min=18, message="Debes tener al menos 18 años.")])
    genero = SelectField(
        "Género",
        choices=[
            ("Masculino", "Masculino"),
            ("Femenino", "Femenino"),
            ("No Binario", "No Binario"),
            ("Transgénero", "Transgénero"),
            ("Agénero", "Agénero"),
            ("Género Fluido", "Género Fluido"),
            ("Otro", "Otro"),
        ],
        validators=[DataRequired()],
        coerce=str
    )
    pais = StringField("País", validators=[DataRequired()])
    ciudad = StringField("Ciudad", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirmar Contraseña", validators=[DataRequired(), EqualTo("password", message="Las contraseñas deben coincidir.")])
    submit = SubmitField("Registrarse")

class PublicacionForm(FlaskForm):
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    imagen = FileField('Subir Imagen', validators=[DataRequired()])
    submit = SubmitField('Publicar')