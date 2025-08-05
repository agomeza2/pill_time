from flask import Flask, request, Response, redirect, url_for, render_template_string, send_file
from functools import wraps
import sqlite3
import csv
import io
from config import WEB_USERNAME, WEB_PASSWORD

app = Flask(__name__)

# Basic AUTH
def check_auth(username, password):
    return username == WEB_USERNAME and password == WEB_PASSWORD

def authenticate():
    return Response(
        'Acceso restringido.\n',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Requerido"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

#  DB 
def get_data():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medi_data ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ROUTE
@app.route("/")
@requires_auth
def index():
    data = get_data()
    return render_template_string(TEMPLATE, data=data)

# CSV 
@app.route("/download")
@requires_auth
def download():
    data = get_data()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Taken_Pill', 'Blood_Pressure'])
    for row in data:
        writer.writerow(row)
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=medi_data.csv"})

# HTML + CHART.JS 
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Registros de Salud</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; padding: 20px; max-width: 800px; margin: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ccc; text-align: center; }
        a.button { display: inline-block; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;}
    </style>
</head>
<body>
    <h1> Registros de Salud</h1>
    <a href="/download" class="button">⬇️ Descargar CSV</a>
    <canvas id="chart" width="400" height="200"></canvas>

    <table>
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Medicamento</th>
                <th>Presión</th>
            </tr>
        </thead>
        <tbody>
            {% for row in data %}
                <tr>
                    <td>{{ row[0] }}</td>
                    <td>{{ '✅' if row[1] else '❌' }}</td>
                    <td>{{ row[2] }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ data|map(attribute=0)|list|reverse }},
                datasets: [{
                    label: 'Presión Arterial',
                    data: {{ data|map(attribute=2)|list|reverse }},
                    borderColor: 'blue',
                    fill: false,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

# --- INICIO ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
