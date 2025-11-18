from flask import Flask, request, jsonify, render_template
import psycopg2
from dotenv import load_dotenv
import os
import requests

load_dotenv()
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

app = Flask(__name__)

# 1. ACTUALIZACIÓN URL EXTERNA (Sin slash al final)
EXTERNAL_API_URL = "https://flask-hello-world-alpha-ebon.vercel.app/sensor"

def get_connection():
    try:
        return psycopg2.connect(CONNECTION_STRING)
    except Exception as e:
        print(f"Error conectando a DB: {e}")
        return None

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'

# ---------------------------------------------------------
# RUTAS API / SENSOR
# ---------------------------------------------------------

# NUEVA RUTA: Obtener TODOS los sensores en JSON
@app.route('/sensor/all')
def get_all_sensors():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor()
        # Obtenemos el ÚLTIMO valor registrado para CADA sensor
        query = """
            SELECT DISTINCT ON (sensor_id) sensor_id, value, created_at 
            FROM sensores 
            ORDER BY sensor_id, created_at DESC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "name": f"Sensor {row[0]}",
                "value": row[1],
                "timestamp": row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else None,
                # Valores simulados (humedad/voltaje) ya que la tabla solo tiene 'value'
                "humidity": 45 + (row[0] * 2), 
                "voltage": 3.3
            })
            
        cur.close()
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# RUTA ACTUALIZADA: Maneja POST, GET (HTML) y GET (JSON)
@app.route("/sensor/<int:sensor_id>", methods=["GET", "POST"])
def sensor_handler(sensor_id):
    # --- MANEJO POST (Insertar datos) ---
    if request.method == "POST":
        value = request.args.get("value", type=float)
        if value is None:
            return jsonify({"error": "Missing 'value' query parameter"}), 400
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO sensores (sensor_id, value) VALUES (%s, %s)", (sensor_id, value))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": "Inserted", "sensor_id": sensor_id, "value": value}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # --- MANEJO GET (Leer datos) ---
    else:
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
            cur.close()
            conn.close()

            # Si el Dashboard pide JSON, devolvemos JSON
            if request.args.get('json'):
                if rows:
                    latest = rows[0]
                    return jsonify({
                        "id": sensor_id,
                        "name": f"Sensor {sensor_id}",
                        "value": latest[0],
                        "timestamp": latest[1].strftime('%Y-%m-%d %H:%M:%S'),
                        "humidity": 50, # Dato simulado
                        "voltage": 3.3  # Dato simulado
                    })
                else:
                    return jsonify({"error": "No data found"}), 404

            # Si es un navegador normal, devolvemos HTML
            values = [r[0] for r in rows][::-1]
            timestamps = [r[1].strftime('%Y-%m-%d %H:%M:%S') for r in rows][::-1]
            return render_template("sensor.html", sensor_id=sensor_id, values=values, timestamps=timestamps, rows=rows)
            
        except Exception as e:
            if request.args.get('json'):
                return jsonify({"error": str(e)}), 500
            return f"<h3>Error: {e}</h3>"


@app.route('/sensor')
def sensor_time():
    try:
        connection = get_connection()
        if not connection: return "DB Connection Error"
        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return f"Current Time: {result[0]}"
    except Exception as e:
        return f"Failed to connect: {e}"

@app.route("/users")
def users():
    users = [
        {"name": "Alice", "email": "alice@example.com", "role": "Admin"},
        {"name": "Bob", "email": "bob@example.com", "role": "Editor"},
        {"name": "Charlie", "email": "charlie@example.com", "role": "Viewer"},
    ]
    return render_template("index.html", title="Flask Render Demo", user="Henry", users=users)

# ---------------------------------------------------------
# RUTA DASHBOARD (Lógica Backend)
# ---------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    device_ids = []
    sensor_data = None
    is_all_view = False
    error = None
    
    # 1. Obtener lista de dispositivos para el dropdown
    try:
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT sensor_id FROM sensores ORDER BY sensor_id ASC")
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
                # Llamamos a nuestra nueva ruta /sensor/all
                resp = requests.get(f"{EXTERNAL_API_URL}/all", timeout=5)
                if resp.status_code == 200:
                    sensor_data = resp.json()
                else:
                    error = f"Error obteniendo todos los sensores: {resp.status_code}"
            else:
                # IMPORTANTE: Agregamos ?json=true para evitar el error 500 (que sucedía al recibir HTML)
                resp = requests.get(f"{EXTERNAL_API_URL}/{selected_id}?json=true", timeout=5)
                
                if resp.status_code == 200:
                    sensor_data = resp.json()
                else:
                    error = f"No se encontraron datos para el ID {selected_id}"
                    
        except requests.RequestException as e:
            error = f"Error conectando a la API externa: {str(e)}"
        except Exception as e:
            error = f"Error interno procesando datos: {str(e)}"

    return render_template(
        "dashboard.html",
        device_ids=device_ids,
        selected_id=selected_id,
        data=sensor_data,
        is_all_view=is_all_view,
        error=error
    )

if __name__ == "__main__":
    app.run(debug=True)
