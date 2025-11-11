from flask import Flask, request, jsonify, render_template
import psycopg2
from dotenv import load_dotenv
import os

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

if __name__ == "__main__":
    app.run(debug=True)
