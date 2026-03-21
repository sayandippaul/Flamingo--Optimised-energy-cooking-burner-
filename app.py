from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import pandas as pd
import os

# ================================ SETUP ================================
app = Flask(__name__, static_folder="public")
CORS(app)

# ================================ LOAD DATA ============================
recipes = pd.read_csv("public/datasets/recipes.csv")
steps = pd.read_csv("public/datasets/steps.csv")
energy = pd.read_csv("public/datasets/energy.csv")
custom = pd.read_csv("public/datasets/customization.csv") if os.path.exists("public/datasets/customization.csv") else pd.DataFrame()

# ================================ CLEAN DATA ===========================
recipes['ingredients'] = recipes['ingredients'].fillna('').str.lower()
recipes['core_ingredients'] = recipes['core_ingredients'].fillna('').str.lower().str.split(',')
recipes['optional_ingredients'] = recipes['optional_ingredients'].fillna('').str.lower().str.split(',')

steps['time'] = pd.to_numeric(steps['time'], errors='coerce').fillna(0)
steps['preferred_energy'] = steps['preferred_energy'].fillna('none').str.lower().str.strip()
steps['action'] = steps['action'].fillna('').str.lower().str.strip()

energy['time_factor'] = pd.to_numeric(energy['time_factor'], errors='coerce').fillna(1)
energy['cost_per_unit'] = pd.to_numeric(energy['cost_per_unit'], errors='coerce').fillna(0)
energy['efficiency'] = pd.to_numeric(energy['efficiency'], errors='coerce').fillna(1)
energy['energy_type'] = energy['energy_type'].fillna('').str.lower().str.strip()
energy['action'] = energy['action'].fillna('').str.lower().str.strip()

# ================================ ROUTES =================================
@app.route('/')
def homepage():
    return send_from_directory('public', 'homepage.html')

@app.route('/recipes_page')
def recipes_page():
    return send_from_directory('public', 'recipes.html')

@app.route('/cooking.html')
def cooking_page():
    return send_from_directory('public', 'cooking.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('public', path)

# ================================ API ROUTES ============================

# Get all recipes
@app.route('/recipes', methods=['GET'])
def get_recipes():
    result = []
    for _, row in recipes.iterrows():
        result.append({
            "id": row['recipe_id'],
            "name": row['recipe_name'],
            "core": [i.strip() for i in row['core_ingredients'] if i.strip()],
            "optional": [i.strip() for i in row['optional_ingredients'] if i.strip()],
            "base_servings": row.get('base_servings', 1)
        })
    return jsonify(result)

# Get unique ingredients
@app.route('/ingredients', methods=['GET'])
def get_ingredients():
    all_ingredients = set()
    for ingr_list in recipes['ingredients'].str.split(','):
        all_ingredients.update([i.strip() for i in ingr_list if i])
    return jsonify(sorted(list(all_ingredients)))

# Calculate cooking method based on gas weight
@app.route('/method', methods=['POST'])
def calculate_method():
    data = request.json
    weight = float(data.get('gas_weight', 0))
    method = 2 if weight < 20 else 3
    return jsonify({"method": method})

# Predict recipes based on ingredients
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    user_ingredients = set([i.lower() for i in data.get("ingredients", [])])
    required_servings = float(data.get("servings", 1))

    results = []
    for _, row in recipes.iterrows():
        core = set([x.strip() for x in row['core_ingredients'] if x.strip()])
        optional = set([x.strip() for x in row['optional_ingredients'] if x.strip()])

        if not core.issubset(user_ingredients):
            continue

        optional_match = (len(optional & user_ingredients) / len(optional)) if len(optional) > 0 else 0
        final_score = 0.5 + 0.3 * optional_match + 0.2 * 1

        results.append({
            "recipe_id": row['recipe_id'],
            "recipe_name": row['recipe_name'],
            "score": final_score,
            "base_servings": row.get('base_servings', 1)
        })

    if not results:
        return jsonify([])

    results = sorted(results, key=lambda x: x['score'], reverse=True)[:6]

    final_output = []
    for r in results:
        recipe_id = r['recipe_id']
        recipe_steps = steps[steps['recipe_id'] == recipe_id]

        total_time = total_energy = total_cost = 0
        energy_used = {}

        for _, step in recipe_steps.iterrows():
            step_time = float(step['time'])
            total_time += step_time
            action = step['action']
            preferred_energy = step['preferred_energy'] or 'none'

            energy_row = energy[(energy['action'] == action) & (energy['energy_type'] == preferred_energy)]
            if not energy_row.empty:
                e = energy_row.iloc[0]
                energy_val = step_time * e['time_factor'] / (e['efficiency'] + 0.0001)
                cost_val = energy_val * e['cost_per_unit']
                total_energy += energy_val
                total_cost += cost_val
                energy_used[preferred_energy] = energy_used.get(preferred_energy, 0) + energy_val

        final_output.append({
            "recipe_name": r['recipe_name'],
            "total_time": round(total_time, 2),
            "total_energy": round(total_energy, 2),
            "total_cost": round(total_cost, 2),
            "energy_breakdown": {k: round(v,2) for k,v in energy_used.items()},
            "servings": required_servings
        })

    return jsonify(final_output)

@app.route('/recipe', methods=['POST'])
def get_recipe():
    data = request.json
    recipe_name = data.get("name", "").lower()
    required_servings = float(data.get("servings", 1))
    method_choice = int(data.get("method", 3))  # 2 or 3

    # Allowed energies based on method
    if method_choice == 2:
        allowed_energy = ['induction' , None , 'none']
    elif method_choice == 3:
        allowed_energy = ['lpg', 'induction' , None , 'none']
    else:
        allowed_energy = []  # fallback, not used

    # Find the recipe
    recipe_row = recipes[recipes['recipe_name'].str.lower() == recipe_name]
    if recipe_row.empty:
        return jsonify({"error": "Recipe not found"})

    recipe_id = recipe_row.iloc[0]['recipe_id']
    base_servings = recipe_row.iloc[0].get('base_servings', 1)
    scaling_factor = required_servings / base_servings

    # Get steps for recipe
    recipe_steps = steps[steps['recipe_id'] == recipe_id].sort_values(by='step_no')
    total_time = total_energy = total_cost = 0
    final_steps = []

    for _, step in recipe_steps.iterrows():
        action = step['action']
        desc = step['description']

        # Choose preferred energy from allowed_energy only
        preferred_energy = step['preferred_energy'] or allowed_energy[0] if allowed_energy else 'none'
        if preferred_energy not in allowed_energy and allowed_energy:
            preferred_energy = allowed_energy[0]

        base_time = float(step['time'])
        scaled_time = int(base_time * (0.8 + 0.2 * scaling_factor))

        step_energy = step_cost = 0
        energy_row = energy[(energy['action'] == action) & (energy['energy_type'] == preferred_energy)]
        if not energy_row.empty:
            e = energy_row.iloc[0]
            step_energy = (scaled_time * e['time_factor'] / (e['efficiency'] + 0.0001)) * scaling_factor
            step_cost = step_energy * e['cost_per_unit']

        total_time += scaled_time
        total_energy += step_energy
        total_cost += step_cost

        final_steps.append({
            "description": desc,
            "time": scaled_time,
            "energy": round(step_energy, 2),
            "cost": round(step_cost, 2),
            "method": preferred_energy.upper()
        })

    return jsonify({
        "name": recipe_name,
        "total_time": total_time,
        "total_energy": round(total_energy, 2),
        "total_cost": round(total_cost, 2),
        "steps": final_steps
    })

import serial
import time

# ===================== ARDUINO SETUP =====================
# Adjust the COM port and baud rate according to your system
# On Linux/Mac: '/dev/ttyUSB0' or '/dev/ttyACM0'
# On Windows: 'COM3', 'COM4', etc.
ARDUINO_PORT = 'COM3'
BAUD_RATE = 9600
arduino = None

try:
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print("Arduino Connected on", ARDUINO_PORT)
except Exception as e:
    print("Arduino NOT connected:", e)
    arduino = None
# ===================== ARDUINO CONNECTION CHECK (NO CODE REQUIRED) =====================
import serial.tools.list_ports

def is_arduino_connected():
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if (
            "Arduino" in port.description or
            "CH340" in port.description or
            (port.vid is not None and port.vid in [0x2341, 0x1A86])
        ):
            return True

    return False


@app.route('/arduino/check', methods=['GET'])
def arduino_check():
    try:
        if is_arduino_connected():
            return jsonify({"connected": True})
        else:
            return jsonify({"connected": False})
    except Exception as e:
        print("Arduino check error:", e)
        return jsonify({"connected": False})
# Helper function to send commands to Arduino
def send_to_arduino(command):
    if arduino:
        try:
            arduino.write(f"{command}\n".encode())
            return True
        except:
            return False
    return False

# ===================== ARDUINO CONTROL ROUTES =====================

@app.route('/arduino/open_cover', methods=['POST'])
def open_cover():
    send_to_arduino("OPEN_COVER")
    return jsonify({"status": "cover_opened"})

@app.route('/arduino/close_cover', methods=['POST'])
def close_cover():
    send_to_arduino("CLOSE_COVER")
    return jsonify({"status": "cover_closed"})

@app.route('/arduino/lpg_on', methods=['POST'])
def lpg_on():
    send_to_arduino("LPG_ON")
    return jsonify({"status": "lpg_led_on"})

@app.route('/arduino/induction_on', methods=['POST'])
def induction_on():
    send_to_arduino("INDUCTION_ON")
    return jsonify({"status": "induction_led_on"})

@app.route('/arduino/none', methods=['POST'])
def arduino_none():
    send_to_arduino("NONE")
    return jsonify({"status": "all_leds_off"})




# ================================ RUN SERVER ============================
if __name__ == "__main__":
    app.run(debug=False, port=5000)




