const BASE_URL = "http://localhost:5000"; // Backend URL

const predictBtn = document.getElementById("predictBtn");
const chooseBtn = document.getElementById("chooseBtn");
const videoPlayer = document.getElementById("videoPlayer");
const sidePanel = document.getElementById("sidePanel");

let recipesList = [];

// ================= PLAY VIDEO ONCE =================
function playOnce(videoFile) {
    videoPlayer.src = videoFile;
    videoPlayer.loop = false;
    videoPlayer.muted = false;
    videoPlayer.play();
}

// ================= FETCH RECIPES =================
async function fetchRecipes() {
    const res = await fetch(`${BASE_URL}/recipes`);
    recipesList = await res.json();
}

// ================= FETCH INGREDIENTS =================
async function fetchIngredients() {
    const res = await fetch(`${BASE_URL}/ingredients`);
    return await res.json();
}

// ================= CREATE SIDE PANEL =================
async function createSidePanel(isPredict) {
    sidePanel.innerHTML = "";

    // ===== Servings =====
    const servingsLabel = document.createElement("label");
    servingsLabel.textContent = "Servings:";
    const servingsSelect = document.createElement("select");
    for (let i = 1; i <= 6; i++) {
        const opt = document.createElement("option");
        opt.value = i;
        opt.textContent = i;
        servingsSelect.appendChild(opt);
    }
    sidePanel.appendChild(servingsLabel);
    sidePanel.appendChild(servingsSelect);

    // ===== Gas Weight =====
    const gasLabel = document.createElement("label");
    gasLabel.textContent = "Gas Weight (kg):";
    const gasInput = document.createElement("input");
    gasInput.type = "number";
    gasInput.step = "0.1";
    sidePanel.appendChild(gasLabel);
    sidePanel.appendChild(gasInput);

    // ===== Search Input =====
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "Search...";
    sidePanel.appendChild(searchInput);

    // ===== Selection Box =====
    const selectionLabel = document.createElement("label");
    const selectionSelect = document.createElement("select");
    selectionSelect.size = 10;
    selectionSelect.className = "select-box";
    selectionSelect.style.width = "100%";
    selectionSelect.multiple = isPredict; // Allow multiple selection for predict
    sidePanel.appendChild(selectionLabel);
    sidePanel.appendChild(selectionSelect);

    if (isPredict) {
        selectionLabel.textContent = "Select Ingredients (Ctrl/Cmd + click for multiple):";
        const ingredients = await fetchIngredients();

        function updateOptions(filter = "") {
            selectionSelect.innerHTML = "";
            ingredients
                .filter(i => i.toLowerCase().includes(filter.toLowerCase()))
                .forEach(i => {
                    const opt = document.createElement("option");
                    opt.value = i;
                    opt.textContent = i;
                    selectionSelect.appendChild(opt);
                });
        }

        updateOptions();
        searchInput.addEventListener("keyup", e => updateOptions(e.target.value));

        // ===== Predict Recipes Button =====
        const predictRecipesBtn = document.createElement("button");
        predictRecipesBtn.textContent = "Predict Recipes";
        predictRecipesBtn.style.marginTop = "10px";
        sidePanel.appendChild(predictRecipesBtn);

        const predictedContainer = document.createElement("div");
        predictedContainer.style.marginTop = "10px";
        sidePanel.appendChild(predictedContainer);

        predictRecipesBtn.addEventListener("click", async () => {
            const selectedIngredients = Array.from(selectionSelect.selectedOptions).map(o => o.value);
            const servings = parseFloat(servingsSelect.value);

            if (selectedIngredients.length === 0) {
                alert("Select at least one ingredient!");
                return;
            }

            // Call backend predict API
            const res = await fetch(`${BASE_URL}/predict`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ingredients: selectedIngredients, servings: servings })
            });
            const data = await res.json();

            if (!data || data.length === 0) {
                alert("No recipes found for selected ingredients!");
                return;
            }

            // Display predicted recipes
            predictedContainer.innerHTML = "";
            const recipeSelect = document.createElement("select");
            recipeSelect.size = 6;
            recipeSelect.className = "select-box";
            predictedContainer.appendChild(recipeSelect);

            data.forEach(r => {
                const opt = document.createElement("option");
                opt.value = r.recipe_name;
                opt.textContent = `${r.recipe_name} (for ${r.servings} servings) ⏱ ${r.total_time} mins 🔋 ${r.total_energy} 💰 ₹${r.total_cost}`;
                recipeSelect.appendChild(opt);
            });

            // Start Cooking Button
            const startBtn = document.createElement("button");
            startBtn.textContent = "Start Cooking";
            startBtn.style.marginTop = "10px";
            predictedContainer.appendChild(startBtn);

            startBtn.addEventListener("click", async () => {
                const selectedRecipe = recipeSelect.value;
                const gasWeight = parseFloat(gasInput.value) || 0;
                if(!gasWeight){
                    alert("Enter gas weight to find the optimized energy");
                    return;
               
                }
                if (!selectedRecipe) {
                    alert("Select a recipe!");
                    return;
                }

                // Call method API
                const methodRes = await fetch(`${BASE_URL}/method`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ gas_weight: gasWeight })
                });
                const methodData = await methodRes.json();

                const jsonData = {
                    name: selectedRecipe,
                    servings: parseInt(servings),
                    method: methodData.method
                };

                localStorage.setItem("cookingData", JSON.stringify(jsonData));
                window.location.href = `${BASE_URL}/cooking.html`;
            });
        });

    } else {
        // ===== Choose Recipe Mode =====
        selectionLabel.textContent = "Select Recipe:";
        function updateOptions(filter = "") {
            selectionSelect.innerHTML = "";
            recipesList
                .filter(r => r.name.toLowerCase().includes(filter.toLowerCase()))
                .forEach(r => {
                    const opt = document.createElement("option");
                    opt.value = r.name;
                    opt.textContent = r.name;
                    selectionSelect.appendChild(opt);
                });
        }
        updateOptions();
        searchInput.addEventListener("keyup", e => updateOptions(e.target.value));

        const startBtn = document.createElement("button");
        startBtn.textContent = "Start Cooking";
        startBtn.style.marginTop = "10px";
        sidePanel.appendChild(startBtn);

        startBtn.addEventListener("click", async () => {
            const selectedRecipe = selectionSelect.value;
            const gasWeight = parseFloat(gasInput.value) || 0;
            const servings = parseInt(servingsSelect.value);

            if (!selectedRecipe) {
                alert("Select a recipe!");
                return;
            }

            const methodRes = await fetch(`${BASE_URL}/method`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ gas_weight: gasWeight })
            });
            const methodData = await methodRes.json();

            const jsonData = {
                name: selectedRecipe,
                servings: servings,
                method: methodData.method
            };

            localStorage.setItem("cookingData", JSON.stringify(jsonData));
            window.location.href = `${BASE_URL}/cooking.html`;
        });
    }
}

// ================= BUTTON HANDLERS =================
predictBtn.addEventListener("click", async () => {
    await fetchRecipes();
    playOnce("/videos/recipe_prediction.mp4");
    createSidePanel(true);
});

chooseBtn.addEventListener("click", async () => {
    await fetchRecipes();
    playOnce("/videos/choose_recipe.mp4");
    createSidePanel(false);
});
