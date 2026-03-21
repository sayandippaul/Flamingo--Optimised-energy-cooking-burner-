from flask import Flask, jsonify, send_from_directory, request
import pandas as pd

app = Flask(__name__, static_folder="public")

# ================================
# 1. LOAD DATA
# ================================
recipes = pd.read_csv("public/datasets/recipes.csv")
steps = pd.read_csv("public/datasets/steps.csv")
energy = pd.read_csv("public/datasets/energy.csv")

# ================================
# 2. DATA CLEANING
# ================================
recipes['ingredients'] = recipes['ingredients'].fillna('').str.lower()
recipes['core_ingredients'] = recipes['core_ingredients'].fillna('').str.lower().str.split(',')
recipes['optional_ingredients'] = recipes['optional_ingredients'].fillna('').str.lower().str.split(',')

steps['time'] = pd.to_numeric(steps['time'], errors='coerce').fillna(0)
energy['time_factor'] = pd.to_numeric(energy['time_factor'], errors='coerce').fillna(1)
energy['cost_per_unit'] = pd.to_numeric(energy['cost_per_unit'], errors='coerce').fillna(0)
energy['efficiency'] = pd.to_numeric(energy['efficiency'], errors='coerce').fillna(1)

# ================================
# 3. ROUTES
# ================================

@app.route('/')
def home():
    return send_from_directory('public', 'recipes.html')

@app.route('/cooking.html')
def cooking_page():
    return send_from_directory('public', 'cooking.html')

# Static files
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('public', path)

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
            "base_servings": row['base_servings'] if 'base_servings' in row else 1
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
    if weight < 1:
        method = 2  # low
    else:
        method = 3  # mid/high
    return jsonify({"method": method})

# Predict recipes based on selected ingredients
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    user_ingredients = set([i.lower() for i in data.get("ingredients", [])])
    required_servings = float(data.get("servings", 1))

    results = []

    for _, row in recipes.iterrows():
        core = set([x.strip() for x in row['core_ingredients'] if x.strip()])
        optional = set([x.strip() for x in row['optional_ingredients'] if x.strip()])

        # Skip if core ingredients not satisfied
        if not core.issubset(user_ingredients):
            continue

        # Optional match
        optional_match = (len(optional & user_ingredients) / len(optional)) if len(optional) > 0 else 0
        # Simplified scoring
        final_score = 0.5 + 0.3 * optional_match + 0.2 * 1

        results.append({
            "recipe_id": row['recipe_id'],
            "recipe_name": row['recipe_name'],
            "score": final_score,
            "base_servings": row['base_servings'] if 'base_servings' in row else 1
        })

    if len(results) == 0:
        return jsonify([])

    # Sort top 6
    results = sorted(results, key=lambda x: x['score'], reverse=True)[:6]

    # Calculate time, energy, cost (simplified)
    final_output = []
    for r in results:
        recipe_id = r['recipe_id']
        recipe_steps = steps[steps['recipe_id'] == recipe_id]

        total_time = 0
        total_energy = 0
        total_cost = 0
        energy_used = {}

        for _, step in recipe_steps.iterrows():
            step_time = float(step['time'])
            total_time += step_time

            action = str(step['action']).strip()
            preferred_energy = str(step['preferred_energy']).strip()

            energy_row = energy[
                (energy['action'].str.strip() == action) &
                (energy['energy_type'].str.strip() == preferred_energy)
            ]
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

# ================================
# RUN SERVER
# ================================
if __name__ == "__main__":
    app.run(debug=True)
