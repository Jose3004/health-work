from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import sqlite3
import logging
import pytz


app = Flask(__name__)

app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '10ea8015a55b69'
app.config['MAIL_PASSWORD'] = 'bded6324c825d6'
app.config['MAIL_DEFAULT_SENDER'] = 'citas@healthywork.com'

mail = Mail(app)
logging.basicConfig(level=logging.DEBUG)
app.secret_key = "clave_super_secreta"  # cámbiala por algo seguro
#####################
# ========================
# Función para conectar BD
# ========================
def get_db():
    conn = sqlite3.connect("instance/healthy.db")
    conn.row_factory = sqlite3.Row
    return conn
# ========================
# Ruta de inicio (login)
# ========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        print("Form recibido:", request.form)

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        # Validación: usuario no existe
        if not user:
            flash("Este usuario no existe.", "error")
            return render_template("login.html")

        # Validación: contraseña incorrecta
        if not check_password_hash(user["password"], password):
            flash("Contraseña incorrecta.", "error")
            return render_template("login.html")

        # Si todo está bien:
        session["user_id"] = user["id"]
        session["user_name"] = user["nombre"]   # Aquí guardas el nombre real

        return redirect(url_for("dashboard"))

    return render_template("login.html")
# ========================
# Registro
# ========================
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        area = request.form["area"]

        print("Datos recibidos:", nombre, email, area)

        hash_pass = generate_password_hash(password)

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO usuarios (nombre, email, password, area) VALUES (?, ?, ?, ?)",
                (nombre, email, hash_pass, area),
            )
            conn.commit()
            print("Usuario guardado correctamente")
            flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError as e:
            print("Error de integridad:", e)
            flash("El correo ya está registrado.", "error")
        finally:
            conn.close()

    return render_template("registro.html")
# ========================
# Dashboard
# ========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", nombre=session.get("nombre"))

# ========================
# Perfil
# ========================
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        nombre = request.form["name"]
        email = request.form["email"]
        area = request.form["area"]

        conn.execute(
            "UPDATE usuarios SET nombre = ?, email = ?, area = ? WHERE id = ?",
            (nombre, email, area, session["user_id"])
        )
        conn.commit()
        conn.close()
        
        # ACTUALIZAR LA SESIÓN INMEDIATAMENTE
        session["nombre"] = nombre
        
        flash("Perfil actualizado correctamente", "success")

        return redirect(url_for("perfil"))

    # GET → consultar datos
    user = conn.execute(
        "SELECT * FROM usuarios WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    
    conn.close()

    return render_template("perfil.html", user=user)
# ========================
# Agenda de citas
# ========================
@app.route("/agenda", methods=["GET", "POST"])
def agenda():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    hoy = date.today().isoformat()

    # Horarios posibles
    horarios_base = [
        "08:00", "09:00", "10:00", "11:00",
        "14:00", "15:00"
    ]

    fecha_seleccionada = request.form.get("fecha")

    horarios_ocupados = []
    if fecha_seleccionada:
        consulta = conn.execute(
            "SELECT hora FROM citas WHERE fecha = ?",
            (fecha_seleccionada,)
        ).fetchall()
        horarios_ocupados = [fila["hora"] for fila in consulta]

    # -----------------------------------------
    # 1. Filtrar horas pasadas si la fecha es hoy
    # -----------------------------------------

    tz = pytz.timezone("America/Bogota")

    if fecha_seleccionada == hoy:
        hora_actual = datetime.now(tz).strftime("%H:%M")
        horarios_base = [h for h in horarios_base if h > hora_actual]

    # -----------------------------------------
    # 2. Filtrar horarios ocupados
    # -----------------------------------------
    horarios_libres = [h for h in horarios_base if h not in horarios_ocupados]

    # -----------------------------------------
    # 3. AQUÍ DEBE IR:
    # -----------------------------------------
    sin_horarios = len(horarios_libres) == 0

    # -----------------------------------------
    # 4. Manejo POST (agendar la cita)
    # -----------------------------------------
    if request.method == "POST" and fecha_seleccionada:
        
        # -----------------------------------------
        # A. Validación: NO permitir fines de semana
        # -----------------------------------------
        dia_semana = datetime.strptime(fecha_seleccionada, "%Y-%m-%d").weekday()  # 0=lunes, 6=domingo
        if dia_semana >= 5:  # 5=sábado, 6=domingo
            flash("No se puede agendar citas los fines de semana.", "error")
            return redirect(url_for("agenda"))

        # -----------------------------------------
        # B. Continuar con el agendamiento normal
        # -----------------------------------------
        hora = request.form["hora"]
        
        conn.execute("""
            INSERT INTO citas (usuario_id, fecha, hora, motivo)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], fecha_seleccionada, hora, "Consulta psicológica"))
        conn.commit()

        user = conn.execute(
            "SELECT email, nombre FROM usuarios WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        enlace = "https://meet.google.com/abc-defg-hij"

        msg = Message(
            subject="Enlace para tu cita psicológica",
            recipients=[user["email"]]
        )

        msg.body = f"""
Hola {user['nombre']},

Tu cita ha sido agendada correctamente.

Fecha: {fecha_seleccionada}
Hora: {hora}

Enlace de la sesión:
{enlace}

Gracias por usar Healthy-Work.
"""

        mail.send(msg)

        flash("Tu cita ha sido agendada y el enlace ha sido enviado a tu correo.", "success")
        return redirect(url_for("agenda"))

    # Cargar citas para mostrar en pantalla
    citas = conn.execute(
        "SELECT * FROM citas WHERE usuario_id = ? ORDER BY fecha, hora",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "agenda.html",
        citas=citas,
        hoy=hoy,
        horarios_libres=horarios_libres,
        sin_horarios=sin_horarios   # <--- AQUÍ YA FUNCIONA
    )

# ========================
# Cerrar sesión
# ========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
# ========================
# Manejo de emociones
# ========================
@app.route("/emociones")
def emociones():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("emociones.html")
# ========================
# Recursos
# ========================
@app.route("/recursos")
def recursos():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("recursos.html")
# ========================
# Horarios disponibles
# ========================
@app.route("/horarios_disponibles")
def horarios_disponibles():
    fecha = request.args.get("fecha")
    if not fecha:
        return {"horarios": []}

    conn = get_db()
    citas = conn.execute(
        "SELECT hora FROM citas WHERE fecha = ?", (fecha,)
    ).fetchall()
    conn.close()

    ocupados = {c["hora"] for c in citas}

    todos = [
        "08:00", "09:00", "10:00", "11:00",
        "14:00", "15:00", "16:00", "17:00"
    ]

    disponibles = [h for h in todos if h not in ocupados]

    return {"horarios": disponibles}

if __name__ == "__main__":
    app.run(debug=True)
