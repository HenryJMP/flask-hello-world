from flask import Flask, request, jsonify  # ✅ You forgot to import request & jsonify
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

app = Flask(__name__)

# ✅ Helper function to get a new DB connection
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
        # ✅ Connect to the database
        connection = get_connection()
        print("Connection successful!")
        
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sensores;")
        result = cursor.fetchone()
        print("Query result:", result)
    
        cursor.close()
        connection.close()
        print("Connection closed.")
        return f"Sensor Data: {result}"
    
    except Exception as e:
        return f"Failed to connect: {e}"

@app.route("/sensor/<int:sensor_id>", methods=["POST"])
def insert_sensor_value(sensor_id):
    # ✅ Get "value" from query string, e.g. ?value=25.3
    value = request.args.get("value", type=float)
    if value is None:
        return jsonify({"error": "Missing 'value' query parameter"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()

        # ✅ Insert into table (make sure the table name & columns exist)
        cur.execute(
            "INSERT INTO sensores (sensor_id, value) VALUES (%s, %s);",
            (sensor_id, value)
        )
        conn.commit()

        cur.close()
        return jsonify({
            "message": "Sensor value inserted successfully",
            "sensor_id": sensor_id,
            "value": value
        }), 201

    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
