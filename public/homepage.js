const loaderContainer = document.getElementById("loaderContainer");
const loaderVideo = document.getElementById("loaderVideo");
const container = document.querySelector(".container");
const frontVideo = document.getElementById("frontVideo");

const popup = document.getElementById("popup");       // First popup
const popupBtn = document.getElementById("popupBtn");

const popup2 = document.getElementById("popup2");     // Second popup
const popup2Btn = document.getElementById("popup2Btn");

const popup3 = document.getElementById("popup3");     // Third popup (end)
const popup3Btn = document.getElementById("popup3Btn");

// ================= LOADER VIDEO =================
loaderVideo.muted = true; // must be muted for autoplay
loaderVideo.play();

// Hide loader after 5 seconds and show main container
setTimeout(() => {
  loaderContainer.style.display = "none";
  container.style.display = "block";

  // Start Flamingo video muted first
  frontVideo.muted = true;
  frontVideo.currentTime = 0;
  frontVideo.pause();

  // Immediately show first popup: Meet Flamingo
  popup.style.display = "flex";

}, 5000);

// ================= FIRST POPUP =================
popupBtn.addEventListener("click", () => {
  popup.style.display = "none";

  // Enable sound after user interaction
  frontVideo.muted = false;
  frontVideo.volume = 1;

  // Play video from start
  frontVideo.currentTime = 0;
  frontVideo.play();

  // After 9 seconds of video, pause and show second popup
  const secondPopupTimer = setInterval(() => {
    if (frontVideo.currentTime >= 9) {
      frontVideo.pause();
      popup2.style.display = "flex"; // show second popup
      clearInterval(secondPopupTimer);
    }
  }, 100);

  // When video fully ends, show third popup
  frontVideo.onended = () => {
    popup3.style.display = "flex";
  };
});

// ================= SECOND POPUP =================
popup2Btn.addEventListener("click", () => {
  popup2.style.display = "none";

  // Continue remaining video
  frontVideo.play();
});

// ================= THIRD POPUP =================
popup3Btn.addEventListener("click", () => {
  popup3.style.display = "none";
  window.location.href = "/recipes_page";
});
