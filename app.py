from flask import Flask, request, jsonify, render_template_string
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB = "reservas.db"

# ---------------- HTML VISUAL -------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ReservasPC</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #333; }
        .pc-container { display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin-bottom: 40px; }
        .pc-card { background: white; padding: 20px; border-radius: 12px; width: 250px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .pc-name { font-size: 1.3em; font-weight: bold; margin-bottom: 10px; }
        .status { font-weight: bold; padding: 5px 10px; border-radius: 5px; color: white; display: inline-block; margin-bottom: 10px; }
        .status.libre { background: green; }
        .status.ocupado { background: red; }
        button { padding: 10px 15px; margin: 5px 0; width: 100%; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button.reservar { background: #007bff; color: white; }
        button.liberar { background: #dc3545; color: white; }
        input { padding: 8px; width: 95%; margin: 5px 0; border-radius: 5px; border: 1px solid #ccc; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #007bff; color: white; }
    </style>
</head>
<body>

<h1>ReservasPC</h1>

<div class="pc-container">
    <div class="pc-card" id="card-Jabalí">
        <div class="pc-name">Jabalí</div>
        <div>Status: <span class="status" id="status-Jabalí">Libre</span></div>
        <input type="date" id="fecha-Jabalí" value="">
        <input type="number" id="duracion-Jabalí" placeholder="Duración (minutos)">
        <button class="reservar" onclick="reservar('Jabalí')">Reservar</button>
        <button class="liberar" onclick="liberar('Jabalí')">Liberar</button>
    </div>

    <div class="pc-card" id="card-Lince">
        <div class="pc-name">Lince</div>
        <div>Status: <span class="status" id="status-Lince">Libre</span></div>
        <input type="date" id="fecha-Lince" value="">
        <input type="number" id="duracion-Lince" placeholder="Duración (minutos)">
        <button class="reservar" onclick="reservar('Lince')">Reservar</button>
        <button class="liberar" onclick="liberar('Lince')">Liberar</button>
    </div>
</div>

<h2>Reservas activas</h2>
<table id="tabla">
    <thead>
        <tr>
            <th>Fecha</th>
            <th>PC</th>
            <th>Usuario</th>
            <th>Fin</th>
        </tr>
    </thead>
    <tbody id="tabla-body">
    </tbody>
</table>

<script>
function todayDateInput(){
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("fecha-Jabalí").value = today;
    document.getElementById("fecha-Lince").value = today;
}
todayDateInput();

function reservar(pc){
    let usuario = prompt("Tu nombre:");
    if(!usuario) return;
    let dur = document.getElementById("duracion-"+pc).value;
    if(!dur) { alert("Ingresa duración"); return; }
    let fecha = document.getElementById("fecha-"+pc).value;

    fetch('/reservar', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({pc:pc, usuario:usuario, dur:dur, fecha:fecha})
    }).then(r=>r.json()).then(d=>{ alert(d.msg); cargar(); })
}

function liberar(pc){
    let usuario = prompt("Tu nombre (para liberar):");
    if(!usuario) return;

    fetch('/liberar', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({pc:pc, usuario:usuario})
    }).then(r=>r.json()).then(d=>{ alert(d.msg); cargar(); })
}

function cargar(){
    fetch('/reservas').then(r=>r.json()).then(data=>{
        // Actualiza tabla
        let html="";
        data.forEach(r=>{
            html += `<tr><td>${r.fecha}</td><td>${r.pc}</td><td>${r.usuario}</td><td>${r.fin}</td></tr>`;
        });
        document.getElementById("tabla-body").innerHTML = html;

        // Actualiza status de PCs
        ['Jabalí','Lince'].forEach(pc=>{
            let res = data.find(x=>x.pc===pc);
            let statusEl = document.getElementById("status-"+pc);
            if(res){
                statusEl.textContent = "Ocupado";
                statusEl.className = "status ocupado";
            }else{
                statusEl.textContent = "Libre";
                statusEl.className = "status libre";
            }
        });
    })
}
cargar();
</script>

</body>
</html>
"""

# ---------------- DB -------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS reservas(
        pc TEXT,
        usuario TEXT,
        fecha TEXT,
        inicio TEXT,
        fin TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

def leer():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT pc, usuario, fecha, inicio, fin FROM reservas")
    res = c.fetchall()
    conn.close()
    return res

def escribir(pc, usuario, fecha, inicio, fin):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM reservas WHERE pc=? AND fecha=?", (pc, fecha))
    c.execute("INSERT INTO reservas VALUES(?,?,?,?,?)",
              (pc, usuario, fecha, inicio, fin))
    conn.commit()
    conn.close()

def borrar(pc, usuario):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM reservas WHERE pc=? AND usuario=?", (pc, usuario))
    conn.commit()
    conn.close()

# ---------------- RUTAS -------------------
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/reservas")
def reservas():
    data = leer()
    lista = []
    for pc, usuario, fecha, inicio, fin in data:
        lista.append({
            "pc": pc,
            "usuario": usuario,
            "fecha": fecha,
            "inicio": inicio,
            "fin": fin.split("T")[1][:5]  # HH:MM
        })
    return jsonify(lista)

@app.route("/reservar", methods=["POST"])
def reservar():
    d = request.json
    pc = d["pc"]
    usuario = d["usuario"]
    dur = int(d["dur"])
    fecha = d["fecha"]

    inicio = datetime.now()
    fin = inicio + timedelta(minutes=dur)

    escribir(pc, usuario, fecha, inicio.isoformat(), fin.isoformat())
    return jsonify({"msg": f"{pc} reservado por {usuario} hasta las {fin.strftime('%H:%M')} del {fecha}"})


@app.route("/liberar", methods=["POST"])
def liberar():
    d = request.json
    pc = d["pc"]
    usuario = d["usuario"]

    borrar(pc, usuario)
    return jsonify({"msg": f"{pc} liberado"})

if __name__ == "__main__":
    app.run()
