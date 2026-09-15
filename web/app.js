const text = document.getElementById("text");
const counter = document.getElementById("counter");

const speed = document.getElementById("speed");
const speedValue = document.getElementById("speedValue");

const generateBtn = document.getElementById("generateBtn");
const pauseBtn = document.getElementById("pauseBtn");
const stopBtn = document.getElementById("stopBtn");
const saveBtn = document.getElementById("saveBtn");

const audio = document.getElementById("audio");
const status = document.getElementById("status");
const themeBtn = document.getElementById("themeBtn");

let audioUrl = null;

// Matn belgilarini sanash
text.addEventListener("input", () => {
  counter.textContent = `${text.value.length} / 5000`;
});

// Tezlik
speed.addEventListener("input", () => {
  speedValue.textContent = `${Number(speed.value).toFixed(1)}x`;

  audio.playbackRate = Number(speed.value);
});

// Ovoz yaratish
generateBtn.addEventListener("click", async () => {
  const value = text.value.trim();

  if (!value) {
    status.textContent = "⚠️ Avval matn kiriting.";
    return;
  }

  generateBtn.disabled = true;
  status.textContent = "⏳ Ovoz tayyorlanmoqda...";

  try {
    const response = await fetch("http://127.0.0.1:8000/tts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: value,
        voice: "asal",
        speed: Number(speed.value)
      })
    });

    if (!response.ok) {
      throw new Error("Server xatosi");
    }

    const blob = await response.blob();

    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }

    audioUrl = URL.createObjectURL(blob);

    audio.src = audioUrl;
    audio.playbackRate = Number(speed.value);

    status.textContent = "✅ Ovoz tayyor!";
    await audio.play();

  } catch (error) {
    console.error(error);

    status.textContent =
      "❌ Server bilan bog‘lanib bo‘lmadi.";
  } finally {
    generateBtn.disabled = false;
  }
});

// Pauza / davom ettirish
pauseBtn.addEventListener("click", () => {
  if (!audio.src) {
    status.textContent = "⚠️ Avval ovoz yarating.";
    return;
  }

  if (audio.paused) {
    audio.play();
    pauseBtn.textContent = "⏸️ Pauza";
    status.textContent = "▶️ Ovoz davom etmoqda...";
  } else {
    audio.pause();
    pauseBtn.textContent = "▶️ Davom";
    status.textContent = "⏸️ Ovoz pauzada.";
  }
});

// To‘xtatish
stopBtn.addEventListener("click", () => {
  audio.pause();
  audio.currentTime = 0;
  pauseBtn.textContent = "⏸️ Pauza";

  status.textContent = "⏹️ Ovoz to‘xtatildi.";
});

// Saqlash
saveBtn.addEventListener("click", () => {
  if (!audioUrl) {
    status.textContent = "⚠️ Avval ovoz yarating.";
    return;
  }

  const link = document.createElement("a");

  link.href = audioUrl;
  link.download = "sado-tts.wav";

  document.body.appendChild(link);
  link.click();
  link.remove();

  status.textContent = "💾 Audio saqlanmoqda...";
});

// Dark / Light
themeBtn.addEventListener("click", () => {
  document.documentElement.classList.toggle("light");

  if (document.documentElement.classList.contains("light")) {
    themeBtn.textContent = "☀️";
  } else {
    themeBtn.textContent = "🌙";
  }
});

// Audio tugaganda
audio.addEventListener("ended", () => {
  pauseBtn.textContent = "⏸️ Pauza";
  status.textContent = "✅ Ovoz tugadi.";
});
