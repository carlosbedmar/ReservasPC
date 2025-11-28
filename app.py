from flask import Flask, render_template_string, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_FILE = "reservas.db"

# Crear la tabla si no existe
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

# HTML de la app
HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Reservas PC</title>
<style>
body { font-family: Arial; background: #f7f7f7; padding: 20px; }
h1 { color: #333; }
input, select { padding: 5px; margin: 5px; }
table { border-collapse: collapse; width: 100%; margin-top: 20px; }
th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
th { background: #eee; }
button { padding: 8px 12px; margin-top: 10px; background: #4CAF50; color: white; border: none; cursor: pointer; }
button:hover { background: #45a049; }
</style>
</head>
<body>
<h1>Reservas de PCs</h1>
<form method="POST">
    <label>Nombre:</label>
    <input type="text" name="usuario" required>
    <label>PC:</label>
    <select name="pc">
        <option value="Jabalí">Jabalí</option>
        <option value="Lince">Lince</option>
    </select>
    <label>Fecha:</label>
    <input type="date" name="fecha" value="{{ hoy }}" required>
    <label>Hora inicio:</label>
    <input type="time" name="hora_inicio" required>
    <label>Hora fin:</label>
    <input type="time" name="hora_fin" required>
    <button type="submit">Reservar</button>
</form>

<h2>Reservas Activas</h2>
<table>
    <tr>
        <th>PC</th>
        <th>Usuario</th>
        <th>Fecha</th>
        <th>Hora inicio</th>
        <th>Hora fin</th>
    </tr>
    {% for r in reservas %}
    <tr>
        <td>{{ r[1] }}</td>
        <td>{{ r[2] }}</td>
        <td>{{ r[3] }}</td>
        <td>{{ r[4] }}</td>
        <td>{{ r[5] }}</td>
    </tr>
    {% endfor %}
</table>
</body>
</html>
'''

# Función para comprobar conflictos
def hay_conflicto(pc, fecha, hora_inicio, hora_fin):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    SELECT * FROM reservas WHERE pc=? AND fecha=? AND NOT (hora_fin <= ? OR hora_inicio >= ?)
    ''', (pc, fecha, hora_inicio, hora_fin))
    conflicto = c.fetchone()
    conn.close()
    return conflicto is not None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        usuario = request.form["usuario"]
        pc = request.form["pc"]
        fecha = request.form["fecha"]
        hora_inicio = request.form["hora_inicio"]
        hora_fin = request.form["hora_fin"]

        # Validar conflictos
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
    hoy = datetime.now().strftime("%Y-%m-%d")
    return render_template_string(HTML, reservas=reservas, hoy=hoy)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
