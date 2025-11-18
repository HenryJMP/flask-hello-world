import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# ------------------------------------------------------------------------------
# 1. CONFIGURACIÓN Y DATOS SIMULADOS (Backend Logic)
# ------------------------------------------------------------------------------

API_BASE_URL = "https://sensor-api-silk.vercel.app/sensor"

def get_device_ids_from_db():
    """
    Simula la consulta a la base de datos para obtener los IDs.
    En producción, aquí iría tu consulta SQL o ORM (SQLAlchemy).
    """
    # Retornamos una lista de IDs que sabemos que existen en la API de ejemplo
    return [1, 2, 3, 4]

def fetch_device_data(device_id):
    """
    Consulta la API externa para obtener datos de un sensor específico.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/{device_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.RequestException as e:
        print(f"Error conectando a la API: {e}")
        return None

# ------------------------------------------------------------------------------
# 2. TEMPLATE HTML (Frontend)
# ------------------------------------------------------------------------------
# Usamos render_template_string para mantener todo en un archivo por simplicidad.
# En tu proyecto real, esto iría en 'templates/dashboard.html'.

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard IoT</title>
    <!-- Tailwind CSS para estilos rápidos y responsivos -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Iconos -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
</head>
<body class="bg-gray-100 min-h-screen font-sans">

    <!-- Navbar -->
    <nav class="bg-blue-600 text-white p-4 shadow-md">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold"><i class="fas fa-microchip mr-2"></i>IoT Monitor</h1>
            <span class="text-sm opacity-80">Estado del Sistema: En línea</span>
        </div>
    </nav>

    <div class="container mx-auto p-6">
        
        <!-- Sección de Control (Formulario) -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <form action="/dashboard" method="GET" class="flex flex-col md:flex-row items-end gap-4">
                <div class="w-full md:w-1/3">
                    <label for="device_id" class="block text-sm font-medium text-gray-700 mb-2">Seleccionar Dispositivo</label>
                    <div class="relative">
                        <select name="device_id" id="device_id" class="block w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white">
                            <option value="" disabled {% if not selected_id %}selected{% endif %}>-- Elige una opción --</option>
                            <option value="all" {% if selected_id == 'all' %}selected{% endif %}>Mostrar Todos</option>
                            {% for dev_id in device_ids %}
                                <option value="{{ dev_id }}" {% if selected_id ==AsString(dev_id) %}selected{% endif %}>
                                    Sensor ID: {{ dev_id }}
                                </option>
                            {% endfor %}
                        </select>
                        <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                            <i class="fas fa-chevron-down"></i>
                        </div>
                    </div>
                </div>
                <button type="submit" class="w-full md:w-auto bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-md transition duration-300 flex items-center justify-center">
                    <i class="fas fa-search mr-2"></i> Mostrar Datos
                </button>
            </form>
        </div>

        <!-- Sección de Visualización de Datos -->
        {% if error %}
            <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6" role="alert">
                <p class="font-bold">Error</p>
                <p>{{ error }}</p>
            </div>
        {% endif %}

        {% if data %}
            {% if is_all_view %}
                <!-- VISTA: TODOS LOS DISPOSITIVOS (Tabla/Grid) -->
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Resumen General de Dispositivos</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {% for sensor in data %}
                        <div class="bg-white rounded-lg shadow hover:shadow-lg transition duration-300 overflow-hidden border-t-4 border-blue-500">
                            <div class="p-5">
                                <div class="flex justify-between items-start mb-4">
                                    <h3 class="text-lg font-bold text-gray-900">{{ sensor.name }}</h3>
                                    <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded">ID: {{ sensor.id }}</span>
                                </div>
                                <div class="space-y-2 text-gray-600">
                                    <p><i class="fas fa-thermometer-half w-6 text-center"></i> Temp: <span class="font-mono text-black">{{ sensor.value }}°C</span></p>
                                    <p><i class="fas fa-tint w-6 text-center"></i> Humedad: <span class="font-mono text-black">{{ sensor.humidity }}%</span></p>
                                    <p><i class="fas fa-bolt w-6 text-center"></i> Voltaje: <span class="font-mono text-black">{{ sensor.voltage }}V</span></p>
                                </div>
                                <div class="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between items-center">
                                    <span><i class="far fa-clock"></i> Última act:</span>
                                    <span>{{ sensor.timestamp }}</span>
                                </div>
                            </div>
                        </div>
                    {% endfor %}
                </div>

            {% else %}
                <!-- VISTA: DISPOSITIVO ÚNICO (Detalle) -->
                <div class="max-w-2xl mx-auto bg-white rounded-xl shadow-md overflow-hidden">
                    <div class="bg-gray-800 p-6 text-white flex justify-between items-center">
                        <div>
                            <h2 class="text-2xl font-bold">{{ data.name }}</h2>
                            <p class="text-gray-400 text-sm">Identificador Único: {{ data.id }}</p>
                        </div>
                        <i class="fas fa-satellite-dish text-4xl opacity-50"></i>
                    </div>
                    
                    <div class="p-8">
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
                            <div class="p-4 bg-orange-50 rounded-lg border border-orange-100">
                                <p class="text-gray-500 text-sm uppercase tracking-wide">Temperatura</p>
                                <p class="text-3xl font-bold text-orange-600">{{ data.value }}°C</p>
                            </div>
                            <div class="p-4 bg-blue-50 rounded-lg border border-blue-100">
                                <p class="text-gray-500 text-sm uppercase tracking-wide">Humedad</p>
                                <p class="text-3xl font-bold text-blue-600">{{ data.humidity }}%</p>
                            </div>
                            <div class="p-4 bg-green-50 rounded-lg border border-green-100">
                                <p class="text-gray-500 text-sm uppercase tracking-wide">Energía</p>
                                <p class="text-3xl font-bold text-green-600">{{ data.voltage }}V</p>
                            </div>
                        </div>
                        
                        <div class="mt-8 text-center">
                            <p class="text-sm text-gray-500 bg-gray-100 inline-block px-4 py-2 rounded-full">
                                <i class="fas fa-sync-alt fa-spin mr-2"></i> Última sincronización: {{ data.timestamp }}
                            </p>
                        </div>
                    </div>
                </div>
            {% endif %}
        
        {% elif selected_id %}
            <!-- Caso: Se seleccionó algo pero no hay datos -->
            <div class="text-center mt-10 text-gray-500">
                <i class="fas fa-exclamation-circle text-4xl mb-4 text-gray-300"></i>
                <p>No se encontraron datos para la selección actual.</p>
            </div>
        {% else %}
            <!-- Estado Inicial -->
            <div class="text-center mt-20 text-gray-400">
                <i class="fas fa-arrow-up text-4xl mb-4 animate-bounce"></i>
                <p class="text-lg">Selecciona un dispositivo arriba para comenzar.</p>
            </div>
        {% endif %}

    </div>
</body>
</html>
"""

# ------------------------------------------------------------------------------
# 3. RUTAS FLASK
# ------------------------------------------------------------------------------

@app.template_filter('AsString')
def to_string_filter(value):
    return str(value)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    # 1. Obtener lista de dispositivos (Simulando DB)
    device_ids = get_device_ids_from_db()
    
    # 2. Obtener parámetro GET
    selected_id = request.args.get('device_id')
    
    sensor_data = None
    is_all_view = False
    error_message = None

    if selected_id:
        if selected_id == 'all':
            # Lógica para "Todos": Iterar y buscar cada uno
            is_all_view = True
            all_sensors = []
            for dev_id in device_ids:
                data = fetch_device_data(dev_id)
                if data:
                    all_sensors.append(data)
            
            if all_sensors:
                sensor_data = all_sensors
            else:
                error_message = "No se pudieron obtener datos de los sensores."
                
        else:
            # Lógica para ID único
            try:
                # Asegurarnos de que el ID seleccionado es válido/numérico si es necesario
                data = fetch_device_data(selected_id)
                if data:
                    sensor_data = data
                else:
                    error_message = f"No se pudo conectar con el sensor ID {selected_id}"
            except Exception as e:
                error_message = f"Error procesando la solicitud: {str(e)}"

    # 3. Renderizar Template
    return render_template_string(
        HTML_TEMPLATE, 
        device_ids=device_ids, 
        selected_id=selected_id, 
        data=sensor_data, 
        is_all_view=is_all_view,
        error=error_message
    )

@app.route('/')
def index():
    # Redirección simple para comodidad
    return '<a href="/dashboard">Ir al Dashboard</a>'

if __name__ == '__main__':
    # Ejecutar en modo debug
    app.run(debug=True, port=5000)
