from flask import render_template, redirect, url_for, request, flash,  send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import Usuario, Post,costos, Publicacion
from database import db
from forms import RegistroForm, LoginForm, PublicacionForm
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import phonenumbers
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont 
import cv2
import numpy as np
import rembg
import base64


def formatear_numero_whatsapp(pais, numero):
    try:
        # Convertir el nombre del país en código ISO (Ej: "Colombia" -> "CO")
        pais_iso = obtener_codigo_iso(pais)
        
        # Parsear el número usando la región (Ej: CO para Colombia)
        numero_formateado = phonenumbers.parse(numero, pais_iso)

        # Devolver el número en formato internacional (+57 3001234567)
        return phonenumbers.format_number(numero_formateado, phonenumbers.PhoneNumberFormat.E164)
    except:
        return numero  # Si falla, devuelve el número sin cambios

def obtener_codigo_iso(nombre_pais):
    """Convierte un nombre de país en su código ISO de dos letras"""
    import pycountry
    pais_obj = pycountry.countries.get(name=nombre_pais)
    return pais_obj.alpha_2 if pais_obj else "US"  # Retorna "US" si no encuentra el país



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
        if current_user.is_authenticated:  # Si ya está logueado, redirigir al perfil
            return redirect(url_for("perfil", user_id=current_user.id))
    
        form = LoginForm()
        if form.validate_on_submit():
            user = Usuario.query.filter_by(username=form.username.data).first()
    
            if user and user.check_password(form.password.data):
                login_user(user)
                flash("Inicio de sesión exitoso.", "success")
                return redirect(url_for("perfil", user_id=user.id))
            else:
                flash("Usuario o contraseña incorrectos.", "danger")
    
        return render_template("login.html", form=form)
    
    @app.route("/perfil/<int:user_id>")
    def perfil(user_id):
        costo = costos.query.first()
        usuario = Usuario.query.get_or_404(user_id)
        img_destacada = request.args.get('img_destacada')
    
        # Convierte el JSON almacenado en string a lista 
        imagenes_perfil = usuario.carrusel_imagenes
        if isinstance(imagenes_perfil, str):
            imagenes_perfil = json.loads(imagenes_perfil)
        
        imagenes_perfil = imagenes_perfil or []  # Asegura que siempre sea una lista
    
        # Extrae solo los nombres de archivo para la comparación
        imagenes_nombres = [img.split("/")[-1] for img in imagenes_perfil]
    
    
        return render_template("perfil.html", usuario=usuario, imagenes=imagenes_perfil, costo=costo)
    
    @app.route("/perfil/editar/<int:user_id>", methods=["GET", "POST"])
    @login_required
    def editar_perfil(user_id):
        usuario = Usuario.query.get_or_404(user_id)
        if usuario.id != current_user.id:
            flash("No puedes editar otro perfil.", "danger")
            return redirect(url_for("perfil", user_id=current_user.id))
    
        if request.method == "POST":
            # Procesar las imágenes del carrusel
                    # Convierte el JSON almacenado en string a lista 
            imagenes_perfil = usuario.carrusel_imagenes
            if isinstance(imagenes_perfil, str):
                imagenes_perfil = json.loads(imagenes_perfil)
            
            imagenes_perfil = imagenes_perfil or []  # Asegura que siempre sea una lista
        
            # Extrae solo los nombres de archivo para la comparación
            imagenes_nombres = [img.split("/")[-1] for img in imagenes_perfil]
            
            # Mantenemos las imágenes existentes como punto de partida
            carrusel_imagenes = imagenes_perfil.copy() if imagenes_perfil else []
            
            # Iteramos sobre las 3 posibles imágenes del formulario
            for i in range(1, 4):
                imagen = request.files.get(f"imagen{i}")
                
                # Solo procesamos si el usuario subió una nueva imagen
                if imagen and allowed_file(imagen.filename):
                    filename = secure_filename(imagen.filename)
                    filename = f"{datetime.now().timestamp()}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Aseguramos que el directorio existe
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    # Guardamos la nueva imagen
                    imagen.save(save_path)
                    
                    # Actualizamos la posición correspondiente en el carrusel
                    # Si ya existe una imagen en esa posición, la reemplazamos
                    if len(carrusel_imagenes) >= i:
                        carrusel_imagenes[i-1] = filename  # Python usa índices base 0
                    else:
                        carrusel_imagenes.append(filename)

    
            # Obtener la descripción del formulario
            descripcion = request.form.get("descripcion")
            print(f"Descripción recibida: {descripcion}")  # Depuración: Verificar la descripción recibida
    
            # Actualizar la descripción y el número de WhatsApp
            usuario.descripcion = descripcion
            usuario.whatsapp = request.form.get("whatsapp")
            if usuario.whatsapp and usuario.pais:
              usuario.whatsapp = formatear_numero_whatsapp(usuario.pais, usuario.whatsapp)
        
        
            if carrusel_imagenes:
                usuario.carrusel_imagenes = carrusel_imagenes
    
            # Depuración: Verificar los datos antes de guardar
            print(f"Datos a guardar - Descripción: {usuario.descripcion}, WhatsApp: {usuario.whatsapp}, Carrusel: {usuario.carrusel_imagenes}")
            
            
    
            # Guardar en la base de datos
            try:
                db.session.commit()
                print("Datos guardados correctamente en la base de datos.")  # Depuración: Confirmar que se guardó
                flash("Perfil actualizado correctamente.", "success")
            except Exception as e:
                db.session.rollback()
                print(f"Error al guardar en la base de datos: {e}")  # Depuración: Capturar errores
                flash("Hubo un error al actualizar el perfil.", "danger")
    
            return redirect(url_for("perfil", user_id=usuario.id))
    
        return render_template("editarperfil.html", usuario=usuario, carrusel_imagenes=carrusel_imagenes)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Has cerrado sesión.", "info")
        return redirect(url_for("index"))

        
    @app.route("/buscar", methods=["GET"])
    def buscar():
        # Obtener parámetros de búsqueda
        query = request.args.get("query", "").strip()
        ciudad = request.args.get("Ciudad", "").strip()
        edad = request.args.get("Edad", "").strip()
    
        # Obtener ciudades únicas de usuarios que tienen publicaciones
        ciudades_con_publicaciones = db.session.query(Usuario.ciudad).join(Post).filter(Post.tipo == 'publicacion').distinct().all()
        ciudades_con_publicaciones = [c[0] for c in ciudades_con_publicaciones]
    
        # Construir la consulta base para Publicaciones
        resultados = Publicacion.query
        
        # Filtro por término de búsqueda
        if query:
            resultados = resultados.filter(or_(
                Post.contenido.ilike(f"%{query}%"),
                Publicacion.contenido.ilike(f"%{query}%")
            ))
        
        # Filtro por ciudad - usando join una sola vez
        if ciudad or edad:
            resultados = resultados.join(Usuario)
            
            if ciudad:
                resultados = resultados.filter(Usuario.ciudad.ilike(f"%{ciudad}%"))
            
            if edad:
                if edad == "46+":
                    resultados = resultados.filter(Usuario.edad >= 46)
                else:
                    try:
                        edad_min, edad_max = map(int, edad.split('-'))
                        resultados = resultados.filter(Usuario.edad.between(edad_min, edad_max))
                    except (ValueError, AttributeError):
                        pass
    
        # Ordenar resultados por fecha de publicación (más recientes primero)
        resultados = resultados.order_by(Publicacion.date_posted.desc())
    
        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = 10
        resultados_paginados = resultados.paginate(page=page, per_page=per_page)
    
        return render_template("busqueda.html",
                             resultados=resultados_paginados,
                             query=query,
                             ciudad=ciudad,
                             edad=edad,
                             ciudades_con_publicaciones=ciudades_con_publicaciones,
                             title="Resultados de búsqueda")
    

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

    @app.route('/guardar_publicacion', methods=['POST'])
    @login_required
    def guardar_publicacion():
        try:
            # Obtener datos necesarios
            costo = costos.query.first()
            usuario = current_user
            descripcion = request.form.get('descripcion')
            imagen = request.files.get('imagen')
    
            # Validación de imagen
            if not imagen or not allowed_file(imagen.filename):
                flash('Formato de imagen no válido', 'danger')
                return redirect(url_for('perfil', user_id=usuario.id))
    
            # Validar costo de publicación
            if not costo or costo.publicar <= 0:
                flash('Error en configuración de costos', 'danger')
                return redirect(url_for('perfil', user_id=usuario.id))
    
            # Verificar saldo del usuario
            if usuario.token_balance < costo.publicar:
                flash(f'Saldo insuficiente. Necesitas {costo.publicar} BBcoins (tienes {usuario.token_balance})', 'danger')
                return redirect(url_for('perfil', user_id=usuario.id))
    
            # Guardar la imagen
            filename = secure_filename(imagen.filename)
            filename = f"{datetime.now().timestamp()}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            imagen.save(save_path)
    
            # Crear publicación y actualizar saldo
            nueva_publicacion = Post(
                tipo='publicacion',
                contenido=descripcion,
                imagen=filename,
                user_id=usuario.id,
                date_posted=datetime.utcnow(),
                ciudad=usuario.ciudad
            )
    
            # Realizar transacción
            usuario.token_balance -= costo.publicar
            db.session.add_all([nueva_publicacion, usuario])
            db.session.commit()
    
            flash(f'Publicación creada exitosamente! Se descontaron {costo.publicar} BBcoins', 'success')
            return redirect(url_for('perfil', user_id=usuario.id))
    
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la publicación: {str(e)}', 'danger')
            return redirect(url_for('perfil', user_id=usuario.id))
        
  # Ruta para iniciar la compra de tokens
    @app.route('/buy_tokens', methods=['GET', 'POST'])
    @login_required
    def buy_tokens():
        if request.method == 'POST':
            try:
                tokens_quantity = int(request.form.get('tokens_quantity'))
            except (TypeError, ValueError):
                flash("Cantidad de tokens inválida.")
                return redirect(url_for('buy_tokens'))
    
            # Precio unitario por token (ajústalo según corresponda)
            price_per_token = 1.00
            total_price = tokens_quantity * price_per_token
    
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": url_for('execute_payment', _external=True, tokens=tokens_quantity),
                    "cancel_url": url_for('payment_cancelled', _external=True)
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "Tokens para Hotads",
                            "sku": "tokens",
                            "price": f"{price_per_token:.2f}",
                            "currency": "USD",
                            "quantity": tokens_quantity
                        }]
                    },
                    "amount": {
                        "total": f"{total_price:.2f}",
                        "currency": "USD"
                    },
                    "description": f"Compra de {tokens_quantity} tokens para usar en Hotads."
                }]
            })
    
            if payment.create():
                # Se busca la URL de aprobación para redirigir al usuario a PayPal
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = str(link.href)
                        return redirect(approval_url)
                flash("No se encontró la URL de aprobación.")
            else:
                flash("Error al crear el pago: " + payment.error.get('message', ''))
            return redirect(url_for('buy_tokens'))
        return render_template('buy_tokens.html')
    
    # Ruta para ejecutar el pago tras la aprobación en PayPal
    @app.route('/execute')
    @login_required
    def execute_payment():
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        tokens_quantity = request.args.get('tokens', type=int)
    
        if not payment_id or not payer_id:
            flash("Parámetros de pago incorrectos.")
            return redirect(url_for('buy_tokens'))
    
        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            # Actualiza el saldo de tokens del usuario
            current_user.token_balance += tokens_quantity
            db.session.commit()
            flash(f"Pago realizado exitosamente. Se añadieron {tokens_quantity} tokens a tu cuenta.")
            return redirect(url_for('perfil'))  # Ajusta la ruta de perfil según corresponda
        else:
            flash("Error al ejecutar el pago.")
            return redirect(url_for('buy_tokens'))
    
    # Ruta para el caso en que el pago sea cancelado
    @app.route('/payment_cancelled')
    @login_required
    def payment_cancelled():
        flash("El pago fue cancelado.")
        return redirect(url_for('buy_tokens'))
        
        
    
    @app.route('/admin', methods=['GET', 'POST'])
    def admin_costos():
        if request.method == 'POST':
            nuevo_valor = request.form.get('publicar')
            
            try:
                # Convertir a entero y validar
                valor_entero = int(float(nuevo_valor))  # Doble conversión para seguridad
                
                if valor_entero < 0:
                    flash('El valor debe ser positivo', 'error')
                    return redirect(url_for('admin_costos'))
                    
                # Eliminar todos los registros anteriores
                costos.query.delete()
                
                # Crear nuevo registro con el valor actualizado
                nuevo_costo = costos(publicar=valor_entero)
                db.session.add(nuevo_costo)
                db.session.commit()
                
                flash(f'Valor actualizado a {valor_entero} BBcoins', 'success')
            except ValueError:
                flash('Por favor ingrese un número válido', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar: {str(e)}', 'error')
            
            return redirect(url_for('admin_costos'))
        
        # Obtener el valor actual
        valor_actual = costos.query.first()
        return render_template('admin.html', valor_actual=valor_actual)
        
    @app.route('/asignar_tokens', methods=['POST'])
    def asignar_tokens():
      
        
        user_id = request.form.get('user_id')
        tokens = request.form.get('tokens')
        
        try:
            # Validar datos
            user_id = int(user_id)
            tokens = int(tokens)
            
            if tokens <= 0:
                flash('La cantidad de tokens debe ser positiva', 'danger')
                return redirect(url_for('admin_costos'))
            
            # Buscar usuario
            usuario = Usuario.query.get(user_id)
            if not usuario:
                flash('Usuario no encontrado', 'danger')
                return redirect(url_for('admin_costos'))
            
            # Asignar tokens
            usuario.token_balance += tokens
            db.session.commit()
            
            flash(f'Se asignaron {tokens} BBcoins al usuario ID {user_id}', 'success')
            
        except ValueError:
            flash('Datos inválidos. Ingrese números enteros válidos', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al asignar tokens: {str(e)}', 'danger')
        
        return redirect(url_for('admin_costos'))
        


    @app.route('/herramientas', methods=['POST'])
    @login_required
    def procesar_imagen():
        try:
            # Validar que se haya enviado una imagen
            if 'imagen' not in request.files:
                return jsonify({"error": "No se proporcionó imagen"}), 400
                
            file = request.files['imagen']
            
            # Validar archivo
            if file.filename == '':
                return jsonify({"error": "Nombre de archivo vacío"}), 400
                
            if not allowed_file(file.filename):
                return jsonify({"error": "Tipo de archivo no permitido"}), 400
    
            # Obtener tipo de procesamiento
            procesamiento = request.form.get('procesamiento')
            if not procesamiento:
                return jsonify({"error": "No se especificó tipo de procesamiento"}), 400
    
            # Procesar imagen
            img = Image.open(file.stream)
            
            # Diccionario de funciones de procesamiento
            procesadores = {
                'remove_bg': remove_background,
                'enhance': enhance_image,
                'blur_face': detect_and_blur_faces,
                'watermark': lambda x: add_watermark(x, request.form.get('texto', 'MarcaEjemplo'))
            }
            
            if procesamiento not in procesadores:
                return jsonify({"error": "Procesamiento no válido"}), 400
                
            result = procesadores[procesamiento](img)
    
            # Preparar respuesta
            img_io = BytesIO()
            result.save(img_io, 'PNG', quality=90)
            img_io.seek(0)
            
            # Configurar headers para forzar descarga como PNG
            response = send_file(
                img_io,
                mimetype='image/png',
                as_attachment=True,
                download_name='imagen_procesada.png'
            )
            
            # Headers adicionales para evitar caché
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            return response
    
        except Exception as e:
            app.logger.error(f"Error al procesar imagen: {str(e)}")
            return jsonify({"error": "Error interno al procesar la imagen"}), 500
    
    
    # Funciones auxiliares (optimizadas)
    def remove_background(img):
        """Elimina el fondo de la imagen usando rembg"""
        try:
            output = rembg.remove(np.array(img))
            return Image.fromarray(output)
        except Exception as e:
            app.logger.error(f"Error removiendo fondo: {str(e)}")
            raise
    
    def enhance_image(img):
        """Mejora la calidad de la imagen"""
        try:
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            # Mejorar en orden óptimo: contraste -> brillo -> nitidez
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Brightness(img).enhance(1.1)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            
            return img
        except Exception as e:
            app.logger.error(f"Error mejorando imagen: {str(e)}")
            raise
    
    def detect_and_blur_faces(img):
        """Detecta rostros y los difumina"""
        try:
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)  # Parámetros optimizados
            
            for (x, y, w, h) in faces:
                # Asegurar que las coordenadas están dentro de la imagen
                x, y, w, h = max(0, x), max(0, y), min(w, img_cv.shape[1]-x), min(h, img_cv.shape[0]-y)
                if w > 0 and h > 0:  # Solo procesar si hay área válida
                    img_cv[y:y+h, x:x+w] = cv2.GaussianBlur(img_cv[y:y+h, x:x+w], (99, 99), 30)
            
            return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        except Exception as e:
            app.logger.error(f"Error difuminando rostros: {str(e)}")
            raise
    
    def add_watermark(img, text):
        """Agrega marca de agua con transparencia"""
        try:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Tamaño de fuente relativo al tamaño de imagen
            font_size = max(20, int(min(img.size)/20))
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Posición diagonal con transparencia
            for i in range(0, img.size[0], int(img.size[0]/3)):
                for j in range(0, img.size[1], int(img.size[1]/3)):
                    draw.text((i, j), text, font=font, fill=(255, 255, 255, 50))
            
            return Image.alpha_composite(img, watermark)
        except Exception as e:
            app.logger.error(f"Error agregando marca de agua: {str(e)}")
            raise
    
    # Función de ayuda para validar extensiones
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
