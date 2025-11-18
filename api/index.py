from flask import Flask, request, jsonify, render_template
import psycopg2
from dotenv import load_dotenv
import os

EXTERNAL_API_URL = "https://sensor-api-silk.vercel.app/sensor"

load_dotenv()
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(CONNECTION_STRING)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'

@app.route('/sensor')
def sensor():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return f"Current Time: {result[0]}"
    except Exception as e:
        return f"Failed to connect: {e}"

@app.route("/sensor/<int:sensor_id>", methods=["POST"])
def insert_sensor_value(sensor_id):
    value = request.args.get("value", type=float)
    if value is None:
        return jsonify({"error": "Missing 'value' query parameter"}), 400
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO sensores (sensor_id, value) VALUES (%s, %s)", (sensor_id, value))
        conn.commit()
        return jsonify({"message": "Inserted", "sensor_id": sensor_id, "value": value}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/sensor/<int:sensor_id>")
def get_sensor(sensor_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT value, created_at
            FROM sensores
            WHERE sensor_id = %s
            ORDER BY created_at DESC
            LIMIT 10;
        """, (sensor_id,))
        rows = cur.fetchall()
        values = [r[0] for r in rows][::-1]
        timestamps = [r[1].strftime('%Y-%m-%d %H:%M:%S') for r in rows][::-1]
        return render_template("sensor.html", sensor_id=sensor_id, values=values, timestamps=timestamps, rows=rows)
    except Exception as e:
        return f"<h3>Error: {e}</h3>"
    finally:
        conn.close()

@app.route("/users")
def users():
    users = [
        {"name": "Alice", "email": "alice@example.com", "role": "Admin"},
        {"name": "Bob", "email": "bob@example.com", "role": "Editor"},
        {"name": "Charlie", "email": "charlie@example.com", "role": "Viewer"},
    ]
    return render_template("index.html", title="Flask Render Demo", user="Henry", users=users)
    
@app.route("/dashboard")
def dashboard():
    device_ids = []
    sensor_data = None
    is_all_view = False
    error = None
    
    # 1. Obtener lista de dispositivos ÚNICOS desde la BD Local
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            # Asumiendo que quieres listar los IDs que existen en tu tabla 'sensores'
            cur.execute("SELECT DISTINCT sensor_id FROM sensores ORDER BY sensor_id ASC")
            # Convertir lista de tuplas [(1,), (2,)] a lista simple [1, 2]
            device_ids = [row[0] for row in cur.fetchall()]
            cur.close()
            conn.close()
        else:
            error = "No se pudo conectar a la base de datos local."
    except Exception as e:
        error = f"Error DB: {str(e)}"

    # 2. Manejar selección del usuario
    selected_id = request.args.get('device_id')

    if selected_id:
        try:
            if selected_id == 'all':
                is_all_view = True
                sensor_data = []
                # Consultar API Externa para CADA dispositivo encontrado en la DB
                for dev_id in device_ids:
                    resp = requests.get(f"{EXTERNAL_API_URL}/{dev_id}", timeout=2)
                    if resp.status_code == 200:
                        sensor_data.append(resp.json())
            else:
                # Consultar API Externa para UN dispositivo
                resp = requests.get(f"{EXTERNAL_API_URL}/{selected_id}", timeout=2)
                if resp.status_code == 200:
                    sensor_data = resp.json()
                else:
                    error = f"No se encontraron datos en la API externa para el ID {selected_id}"
        except requests.RequestException as e:
            error = f"Error conectando a la API externa: {str(e)}"

    return render_template(
        "dashboard.html",
        device_ids=device_ids,
        selected_id=selected_id, # Para mantener la opción seleccionada en el dropdown
        data=sensor_data,
        is_all_view=is_all_view,
        error=error
    )

if __name__ == "__main__":
    app.run(debug=True)
