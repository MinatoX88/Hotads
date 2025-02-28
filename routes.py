from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import Usuario, Post
from database import db
from forms import RegistroForm, LoginForm, PublicacionForm
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import os
from datetime import datetime

UPLOAD_FOLDER = "static/img/publicaciones"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def init_routes(app, login_manager):
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    @app.route("/")
    def index():
        publicaciones = Post.query.order_by(Post.date_posted.desc()).all()
        return render_template("index.html", publicaciones=publicaciones)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = Usuario.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash("Inicio de sesión exitoso.", "success")
                return redirect(url_for("perfil", user_id=user.id))
            flash("Usuario o contraseña incorrectos.", "danger")
        return render_template("login.html", form=form)

    @app.route("/perfil/<int:user_id>")
    def perfil(user_id):
        usuario = Usuario.query.get_or_404(user_id)
        return render_template("perfil.html", usuario=usuario)
    @app.route("/perfil/editar/<int:user_id>", methods=["GET", "POST"])
    @login_required
    def editar_perfil(user_id):
        usuario = Usuario.query.get_or_404(user_id)
        if usuario.id != current_user.id:
            flash("No puedes editar otro perfil.", "danger")
            return redirect(url_for("perfil", user_id=current_user.id))
    
        if request.method == "POST":
            # Procesar las imágenes del carrusel
            carrusel_imagenes = []
            for i in range(1, 4):
                imagen = request.files.get(f"imagen{i}")
                if imagen and allowed_file(imagen.filename):
                    filename = secure_filename(imagen.filename)
                    filename = f"{datetime.now().timestamp()}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    imagen.save(save_path)
                    carrusel_imagenes.append(filename)
    
            # Actualizar la descripción y el número de WhatsApp
            usuario.descripcion = request.form.get("descripcion")
            usuario.whatsapp = request.form.get("whatsapp")
            if carrusel_imagenes:
                usuario.carrusel_imagenes = carrusel_imagenes
    
            db.session.commit()
            flash("Perfil actualizado correctamente.", "success")
            return redirect(url_for("perfil", user_id=usuario.id))
    
        return render_template("editarperfil.html", usuario=usuario)
    
        @app.route("/logout")
        @login_required
        def logout():
            logout_user()
            flash("Has cerrado sesión.", "info")
            return redirect(url_for("index"))
    
        @app.route("/herramientas")
        @login_required
        def herramientas():
            return render_template("herramientas.html")
    
        @app.route("/buscar", methods=["GET"])
        def buscar():
            query = request.args.get("q")
            ciudad = request.args.get("ciudad")
            edad = request.args.get("edad")
    
            resultados = Publicacion.query
            if query:
                resultados = resultados.filter(or_(
                    Publicacion.titulo.ilike(f"%{query}%"),
                    Publicacion.contenido.ilike(f"%{query}%")
                ))
            if ciudad:
                resultados = resultados.join(Usuario).filter(Usuario.ciudad.ilike(f"%{ciudad}%"))
            if edad:
                resultados = resultados.join(Usuario).filter(Usuario.edad.between(*map(int, edad.split('-'))))
    
            return render_template("resultados_busqueda.html", resultados=resultados.all(), query=query)
    
        @app.route("/privacidad")
        def privacidad():
            return render_template("privacidad.html")
            
    
    
        @app.route("/registro", methods=["GET", "POST"])
        def registro():
            form = RegistroForm()  # Crear una instancia del formulario
            if form.validate_on_submit():
                # Verificar si el usuario ya existe
                if Usuario.query.filter_by(username=form.username.data).first():
                    flash("El nombre de usuario ya está en uso.", "danger")
                    return redirect(url_for("registro"))
    
                # Crear un nuevo usuario
                nuevo_usuario = Usuario(
                    username=form.username.data,
                    edad=form.edad.data,
                    genero=form.genero.data,
                    pais=form.pais.data,
                    ciudad=form.ciudad.data,
                    descripcion=""
                )
                nuevo_usuario.set_password(form.password.data)
    
                # Guardar el usuario en la base de datos
                db.session.add(nuevo_usuario)
                db.session.commit()
    
                # Iniciar sesión automáticamente
                login_user(nuevo_usuario)
                flash("Registro exitoso. ¡Bienvenido!", "success")
                return redirect(url_for("perfil", user_id=nuevo_usuario.id))
    
            # Pasar el formulario a la plantilla
            return render_template("registro.html", form=form)  # ¡Aquí está la corrección! @app.route("/registro")
    
    
        @app.route('/publicar', methods=['GET', 'POST'])
        @login_required  # Solo usuarios logueados pueden acceder
        def publicar():
            form = PublicacionForm()
        
            if form.validate_on_submit():
            # Procesar la imagen subida
                imagen = form.imagen.data
                if imagen:
                # Guardar la imagen en el servidor
                    filename = secure_filename(imagen.filename)
                # Añadir un timestamp al nombre del archivo para evitar colisiones
                    filename = f"{datetime.now().timestamp()}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Crear directorio si no existe
                    imagen.save(save_path)
                else:
                    flash('Debes subir una imagen', 'danger')
                    return redirect(url_for('publicar'))
    
            # Crear la nueva publicación
                nueva_publicacion = Post(
                    tipo='publicacion',  # Asignar el tipo 'publicacion'
                   # Título por defecto
                   contenido=form.descripcion.data,
                   imagen=filename,
                   user_id=current_user.id,
                    date_posted=datetime.utcnow(),
                    ciudad=current_user.ciudad
            )
    
            # Guardar en la base de datos
                db.session.add(nueva_publicacion)
                db.session.commit()
    
                flash('Publicación creada exitosamente', 'success')
                return redirect(url_for('perfil', user_id=current_user.id))
        
            return render_template('publicar.html', form=form)
            
    
        @app.route('/guardar_publicacion', methods=['POST'])
        @login_required  # Solo usuarios logueados pueden publicar
        def guardar_publicacion():
            # Obtener los datos del formulario
            descripcion = request.form.get('descripcion')
            imagen = request.files.get('imagen')
        
            # Validar que se haya subido una imagen
            if not imagen or not allowed_file(imagen.filename):
                flash('Formato de imagen no válido', 'danger')
                return redirect(url_for('perfil', user_id=current_user.id))
        
            # Guardar la imagen en el servidor
            filename = secure_filename(imagen.filename)
            filename = f"{datetime.now().timestamp()}_{filename}"  # Evitar colisiones
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Crear directorio si no existe
            imagen.save(save_path)
        
            # Crear la nueva publicación
            nueva_publicacion = Post(
                tipo='publicacion',  # Tipo de publicación
                 # Título por defecto
                contenido=descripcion,
                imagen=filename,
                user_id=current_user.id,
                date_posted=datetime.utcnow(),
                ciudad=current_user.ciudad
            )
        
            # Guardar en la base de datos
            db.session.add(nueva_publicacion)
            db.session.commit()
        
            flash('Publicación creada exitosamente', 'success')
            return redirect(url_for('perfil', user_id=current_user.id))

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Has cerrado sesión.", "info")
        return redirect(url_for("index"))

    @app.route("/herramientas")
    @login_required
    def herramientas():
        return render_template("herramientas.html")

    @app.route("/buscar", methods=["GET"])
    def buscar():
        query = request.args.get("q")
        ciudad = request.args.get("ciudad")
        edad = request.args.get("edad")

        resultados = Publicacion.query
        if query:
            resultados = resultados.filter(or_(
                Publicacion.titulo.ilike(f"%{query}%"),
                Publicacion.contenido.ilike(f"%{query}%")
            ))
        if ciudad:
            resultados = resultados.join(Usuario).filter(Usuario.ciudad.ilike(f"%{ciudad}%"))
        if edad:
            resultados = resultados.join(Usuario).filter(Usuario.edad.between(*map(int, edad.split('-'))))

        return render_template("resultados_busqueda.html", resultados=resultados.all(), query=query)

    @app.route("/privacidad")
    def privacidad():
        return render_template("privacidad.html")
        


    @app.route("/registro", methods=["GET", "POST"])
    def registro():
        form = RegistroForm()  # Crear una instancia del formulario
        if form.validate_on_submit():
            # Verificar si el usuario ya existe
            if Usuario.query.filter_by(username=form.username.data).first():
                flash("El nombre de usuario ya está en uso.", "danger")
                return redirect(url_for("registro"))

            # Crear un nuevo usuario
            nuevo_usuario = Usuario(
                username=form.username.data,
                edad=form.edad.data,
                genero=form.genero.data,
                pais=form.pais.data,
                ciudad=form.ciudad.data,
                descripcion=""
            )
            nuevo_usuario.set_password(form.password.data)

            # Guardar el usuario en la base de datos
            db.session.add(nuevo_usuario)
            db.session.commit()

            # Iniciar sesión automáticamente
            login_user(nuevo_usuario)
            flash("Registro exitoso. ¡Bienvenido!", "success")
            return redirect(url_for("perfil", user_id=nuevo_usuario.id))

        # Pasar el formulario a la plantilla
        return render_template("registro.html", form=form)  # ¡Aquí está la corrección! @app.route("/registro")


    @app.route('/publicar', methods=['GET', 'POST'])
    @login_required  # Solo usuarios logueados pueden acceder
    def publicar():
        form = PublicacionForm()
    
        if form.validate_on_submit():
        # Procesar la imagen subida
            imagen = form.imagen.data
            if imagen:
            # Guardar la imagen en el servidor
                filename = secure_filename(imagen.filename)
            # Añadir un timestamp al nombre del archivo para evitar colisiones
                filename = f"{datetime.now().timestamp()}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Crear directorio si no existe
                imagen.save(save_path)
            else:
                flash('Debes subir una imagen', 'danger')
                return redirect(url_for('publicar'))

        # Crear la nueva publicación
            nueva_publicacion = Post(
                tipo='publicacion',  # Asignar el tipo 'publicacion'
               # Título por defecto
               contenido=form.descripcion.data,
               imagen=filename,
               user_id=current_user.id,
                date_posted=datetime.utcnow(),
                ciudad=current_user.ciudad
        )

        # Guardar en la base de datos
            db.session.add(nueva_publicacion)
            db.session.commit()

            flash('Publicación creada exitosamente', 'success')
            return redirect(url_for('perfil', user_id=current_user.id))
    
        return render_template('publicar.html', form=form)
        

    @app.route('/guardar_publicacion', methods=['POST'])
    @login_required  # Solo usuarios logueados pueden publicar
    def guardar_publicacion():
        # Obtener los datos del formulario
        descripcion = request.form.get('descripcion')
        imagen = request.files.get('imagen')
    
        # Validar que se haya subido una imagen
        if not imagen or not allowed_file(imagen.filename):
            flash('Formato de imagen no válido', 'danger')
            return redirect(url_for('perfil', user_id=current_user.id))
    
        # Guardar la imagen en el servidor
        filename = secure_filename(imagen.filename)
        filename = f"{datetime.now().timestamp()}_{filename}"  # Evitar colisiones
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Crear directorio si no existe
        imagen.save(save_path)
    
        # Crear la nueva publicación
        nueva_publicacion = Post(
            tipo='publicacion',  # Tipo de publicación
             # Título por defecto
            contenido=descripcion,
            imagen=filename,
            user_id=current_user.id,
            date_posted=datetime.utcnow(),
            ciudad=current_user.ciudad
        )
    
        # Guardar en la base de datos
        db.session.add(nueva_publicacion)
        db.session.commit()
    
        flash('Publicación creada exitosamente', 'success')
        return redirect(url_for('perfil', user_id=current_user.id))