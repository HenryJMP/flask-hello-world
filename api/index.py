from flask import Flask
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
CONNECTION_STRING = os.getenv("CONNECTION_STRING")

# ❌ was _name_ — should be __name__
app = Flask(__name__)

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
        connection = psycopg2.connect(CONNECTION_STRING)
        print("Connection successful!")
        
        # Create a cursor to execute SQL queries
        cursor = connection.cursor()
        
        # Example query (you can change the table name)
        cursor.execute("SELECT * FROM sensores;")
        result = cursor.fetchone()
        print("Query result:", result)
    
        # Close the cursor and connection
        cursor.close()
        connection.close()
        print("Connection closed.")
        return f"Sensor Data: {result}"
    
    except Exception as e:
        return f"Failed to connect: {e}"

# ✅ Add this to run the app
if __name__ == '__main__':
    app.run(debug=True)
