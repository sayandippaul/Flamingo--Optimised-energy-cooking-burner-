const BASE_URL = "http://localhost:5000"; // always use full URL for fetch

let isSoundEnabled = false;

// ================= CHECK ARDUINO CONNECTION =================
let isArduinoConnected = false;

document.addEventListener("DOMContentLoaded", () => {

    async function checkArduinoConnection() {
        try {
            const res = await fetch(`${BASE_URL}/arduino/check`);
            const data = await res.json();

            console.log("Arduino status:", data.connected); // ✅ debug

            if (data.connected && !isArduinoConnected) {
                isArduinoConnected = true;
                alert("Arduino Connected ✅");
            } 
            else if (!data.connected && isArduinoConnected) {
                isArduinoConnected = false;
                alert("Arduino Disconnected ❌");
            }

        } catch (err) {
            console.error("Error:", err);
            if (isArduinoConnected) {
                isArduinoConnected = false;
                alert("Arduino Disconnected ❌");
            }
        }
    }

    // ✅ Run once
    checkArduinoConnection();

    // ✅ Run continuously (IMPORTANT)
    // setInterval(checkArduinoConnection, 10000);
});

// ================= FETCH RECIPE FROM LOCALSTORAGE =================
const storedData = JSON.parse(localStorage.getItem("cookingData") || "{}");
const recipeName = storedData.name || "biryani";
const servings = storedData.servings || 1;
const method = storedData.method || 3;

if (method == 2) {
    document.getElementById("status").innerText = "Cylinder : LOW";
} else {
    document.getElementById("status").innerText = "Cylinder : Medium To High ";
}

fetch(`${BASE_URL}/recipe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        name: recipeName,
        servings: servings,
        method: method
    })
})
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            window.location.href = "/";
        } else {
            startApp(data);
        }
    })
    .catch(err => {
        console.error(err);
        alert("Failed to fetch recipe data.");
    });

// ================= MAIN FUNCTION =================
function startApp(data) {
    const itemName = document.getElementById("itemName");
    const timerEl = document.getElementById("timer");
    const stepsList = document.getElementById("stepsList");
    const energyEl = document.getElementById("energy");
    const methodEl = document.getElementById("method");
    const videoPlayer = document.getElementById("mainVideo");
    const startBtn = document.getElementById("startBtn");

    itemName.innerText = "Item: " + data.name;
    energyEl.innerText = `Total Energy: ${data.total_energy} (₹${data.total_cost})`;

    let currentStep = 0;
    let timeLeft = 0;
    let timerInterval;

    // ================= ENABLE SOUND =================
    startBtn.addEventListener("click", () => {
        isSoundEnabled = true;
        videoPlayer.muted = false;
        videoPlayer.volume = 1;
        startBtn.style.display = "none";
        startCooking();
    });

    // ================= VIDEO PLAYER =================
    function playVideo(src, loop = false, onEndCallback = null) {
        videoPlayer.pause();
        videoPlayer.src = src;
        videoPlayer.load();
        videoPlayer.currentTime = 0;
        videoPlayer.loop = loop;
        videoPlayer.muted = !isSoundEnabled;
        videoPlayer.play().catch(err => console.log(err));
        videoPlayer.onended = onEndCallback || null;
    }

    // ================= STEP UI =================
    function showStep(step) {
        stepsList.innerHTML = "";
        let li = document.createElement("li");
        li.innerText = `${step.description}
⚡ Energy: ${step.energy || 0}
💰 Cost: ₹${step.cost || 0}`;
        stepsList.appendChild(li);
        methodEl.innerText = "Method: " + (step.method || "N/A");
        timeLeft = step.time || 5; // default

        // ============== ARDUINO LED CONTROL =================
        if (isArduinoConnected) {
            if (step.method.toLowerCase() === "lpg") {
                fetch(`${BASE_URL}/arduino/lpg_on`, { method: "POST" });
            } else if (step.method.toLowerCase() === "induction") {
                fetch(`${BASE_URL}/arduino/induction_on`, { method: "POST" });
            } else {
                fetch(`${BASE_URL}/arduino/none`, { method: "POST" });
            }
        }
    }

    // ================= TIMER =================
    function startTimer(callback) {
        timerInterval = setInterval(() => {
            timerEl.innerText = `Time: ${timeLeft}s`;
            timeLeft--;
            if (timeLeft < 0) {
                clearInterval(timerInterval);
                callback();
            }
        }, 1000);
    }

    // ================= FLOW =================
    async function startCooking() {
        stepsList.innerHTML = "<li>🔥 Your gas is opening automatically...</li>";

        if (isArduinoConnected) {
            await fetch(`${BASE_URL}/arduino/open_cover`, { method: "POST" });
        }

        playVideo("public/videos/gas_open.mp4", false, () => playSteps());
    }

    function playSteps() {
        playVideo("public/videos/cooking.mp4", true);
        runStep();
    }

    function runStep() {
        if (!data.steps || currentStep >= data.steps.length) {
            endCooking();
            return;
        }
        let step = data.steps[currentStep];
        showStep(step);
        startTimer(() => {
            currentStep++;
            runStep();
        });
    }

    async function endCooking() {
        stepsList.innerHTML = "<li>🙏 Thank you! Enjoy your dish 🍽️</li>";


        if (isArduinoConnected) {
            await fetch(`${BASE_URL}/arduino/close_cover`, { method: "POST" });
        }

        playVideo("public/videos/gas_close.mp4", false, () => videoPlayer.pause());
        timerEl.innerText = "Cooking Done ✅";
        methodEl.innerText = "Finished";


    }
}

// ================= HOME BUTTON =================
function goHome() {
    window.location.href = "/";
}
