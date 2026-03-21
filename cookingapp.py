# ================================
# IMPORTS
# ================================
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# ================================
# LOAD DATA
# ================================
recipes = pd.read_csv('public/datasets/recipes.csv')
steps = pd.read_csv('public/datasets/steps.csv')
energy = pd.read_csv('public/datasets/energy.csv')
custom = pd.read_csv('public/datasets/customization.csv')

# ================================
# CLEAN DATA
# ================================
steps['time'] = pd.to_numeric(steps['time'], errors='coerce').fillna(0)
steps['preferred_energy'] = steps['preferred_energy'].fillna('none').str.lower().str.strip()

energy['time_factor'] = pd.to_numeric(energy['time_factor'], errors='coerce').fillna(1)
energy['cost_per_unit'] = pd.to_numeric(energy['cost_per_unit'], errors='coerce').fillna(0)
energy['efficiency'] = pd.to_numeric(energy['efficiency'], errors='coerce').fillna(1)

energy['energy_type'] = energy['energy_type'].fillna('').str.lower().str.strip()
energy['action'] = energy['action'].fillna('').str.lower().str.strip()

# ================================
# API ROUTE
# ================================
@app.route('/recipe', methods=['POST'])
def get_recipe():

    data = request.json

    recipe_name = data.get("name", "").lower()
    required_servings = float(data.get("servings", 1))
    method_choice = data.get("method", 3)

    # ENERGY FILTER
    if method_choice == 1:
        allowed_energy = ['lpg']
    elif method_choice == 2:
        allowed_energy = ['induction']
    else:
        allowed_energy = ['lpg', 'induction']

    # ================================
    # FIND RECIPE
    # ================================
    recipe_row = recipes[recipes['recipe_name'].str.lower() == recipe_name]

    if recipe_row.empty:
        return jsonify({"error": "Recipe not found"})

    recipe_id = recipe_row.iloc[0]['recipe_id']
    base_servings = recipe_row.iloc[0].get('base_servings', 1)

    scaling_factor = required_servings / base_servings

    recipe_steps = steps[steps['recipe_id'] == recipe_id].sort_values(by='step_no')

    total_time = 0
    total_energy = 0
    total_cost = 0

    final_steps = []

    # ================================
    # PROCESS STEPS
    # ================================
    for _, step in recipe_steps.iterrows():

        action = str(step['action']).strip().lower()
        desc = str(step['description'])

        preferred_energy = str(step['preferred_energy']).strip().lower()
        if preferred_energy == '' or preferred_energy == 'nan':
            preferred_energy = 'none'

        base_time = float(step['time'])

        # ⏱ CONVERT TO SECONDS
        # scaled_time = int((base_time * (0.8 + 0.2 * scaling_factor)) * 60)
        scaled_time = int((base_time * (0.8 + 0.2 * scaling_factor)) )

        step_energy = 0
        step_cost = 0

        if preferred_energy != 'none':

            if preferred_energy not in allowed_energy:
                preferred_energy = allowed_energy[0]

            energy_row = energy[
                (energy['action'] == action) &
                (energy['energy_type'] == preferred_energy)
            ]

            if not energy_row.empty:
                e = energy_row.iloc[0]

                time_factor = float(e['time_factor'])
                cost_per_unit = float(e['cost_per_unit'])
                efficiency = float(e['efficiency'])

                step_energy = (scaled_time * time_factor / (efficiency + 0.0001)) * scaling_factor
                step_cost = step_energy * cost_per_unit

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

    # ================================
    # RESPONSE
    # ================================
    return jsonify({
        "name": recipe_name,
        "total_time": total_time,
        "total_energy": round(total_energy, 2),
        "total_cost": round(total_cost, 2),
        "steps": final_steps
    })


# ================================
# RUN SERVER
# ================================
if __name__ == '__main__':
    app.run(debug=True)
