from flask import Flask, render_template_string, request, redirect
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB_FILE = "reservas.db"

# Crear tabla si no existe
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pc TEXT NOT NULL,
        usuario TEXT NOT NULL,
        fecha TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# HTML de la app
HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Reservas PC</title>
<style>
body { font-family: Arial; background: #f0f2f5; padding: 20px; }
h1 { color: #333; text-align: center; }
.container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);}
form { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 20px; }
input, select, button { padding: 8px; border-radius: 5px; border: 1px solid #ccc; }
button { background: #4CAF50; color: white; border: none; cursor: pointer; }
button:hover { background: #45a049; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px; text-align: center; border: 1px solid #ddd; }
th { background: #eee; }
.libre { background-color: #c8e6c9; } /* verde */
.ocupado { background-color: #ffcdd2; } /* rojo */
</style>
</head>
<body>
<h1>Reservas de PCs</h1>
<div class="container">
<form method="POST">
    <input type="text" name="usuario" placeholder="Tu nombre" required>
    <select name="pc">
        <option value="Jabalí">Jabalí</option>
        <option value="Lince">Lince</option>
    </select>
    <input type="date" name="fecha" value="{{ hoy }}" required>
    <select name="hora_inicio">
        {% for h in horas %}
        <option value="{{ h }}">{{ h }}</option>
        {% endfor %}
    </select>
    <select name="hora_fin">
        {% for h in horas %}
        <option value="{{ h }}">{{ h }}</option>
        {% endfor %}
    </select>
    <button type="submit">Reservar</button>
</form>

<h2>Estado de PCs</h2>
<table>
<tr><th>PC</th><th>Usuario</th><th>Fecha</th><th>Hora inicio</th><th>Hora fin</th></tr>
{% for r in reservas %}
<tr class="{% if r[3]==hoy %}ocupado{% else %}libre{% endif %}">
    <td>{{ r[1] }}</td>
    <td>{{ r[2] }}</td>
    <td>{{ r[3] }}</td>
    <td>{{ r[4] }}</td>
    <td>{{ r[5] }}</td>
</tr>
{% endfor %}
</table>
</div>
</body>
</html>
'''

# Generar horas en intervalos de 30 minutos
def generar_horas():
    horas = []
    start = datetime.strptime("08:00", "%H:%M")
    end = datetime.strptime("20:00", "%H:%M")
    while start <= end:
        horas.append(start.strftime("%H:%M"))
        start += timedelta(minutes=30)
    return horas

def hay_conflicto(pc, fecha, hora_inicio, hora_fin):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    SELECT * FROM reservas WHERE pc=? AND fecha=? AND NOT (hora_fin <= ? OR hora_inicio >= ?)
    ''', (pc, fecha, hora_inicio, hora_fin))
    conflicto = c.fetchone()
    conn.close()
    return conflicto is not None

@app.route("/", methods=["GET","POST"])
def index():
    hoy = datetime.now().strftime("%Y-%m-%d")
    if request.method == "POST":
        usuario = request.form.get("usuario")
        pc = request.form.get("pc")
        fecha = request.form.get("fecha")
        hora_inicio = request.form.get("hora_inicio")
        hora_fin = request.form.get("hora_fin")

        if not usuario or not pc or not fecha or not hora_inicio or not hora_fin:
            return "<h2>Error: Todos los campos son obligatorios.</h2><a href='/'>Volver</a>"

        if hay_conflicto(pc, fecha, hora_inicio, hora_fin):
            return "<h2>Error: El PC ya está reservado en ese horario.</h2><a href='/'>Volver</a>"

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO reservas (pc, usuario, fecha, hora_inicio, hora_fin) VALUES (?, ?, ?, ?, ?)',
                  (pc, usuario, fecha, hora_inicio, hora_fin))
        conn.commit()
        conn.close()
        return redirect("/")

    # GET: mostrar reservas
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM reservas ORDER BY fecha, hora_inicio')
    reservas = c.fetchall()
    conn.close()
    return render_template_string(HTML, reservas=reservas, hoy=hoy, horas=generar_horas())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

