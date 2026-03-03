/**
 * DeadlineMap ICHEC — main.js  (Game Edition)
 * Confetti · SVG Ring Timer · 3D Card Tilt · Scroll Reveal
 * Mascot reactions · Footer quotes
 */

/* ── Quotes ─────────────────────────────────────────────────── */
const BLOCUS_QUOTES = [
  '"Le bachelier se forge dans la douleur des QCM ratés."',
  '"TikTok sera encore là après les examens. Ta moyenne, non."',
  '"Chaque heure de révision = une question de moins à improviser."',
  '"Les notes ne se font pas pendant les soirées BDE."',
  '"Même Van Damme a dû apprendre ses gammes."',
  '"Focus. ICHEC ne rembourse pas les années doublées."',
  '"Un Pomodoro à la fois. Tu peux le faire."',
  '"Le café ne te sauvera pas. Le cours magistral de 8h, oui."',
];
const FOOTER_QUOTES = [
  "Fait entre deux cours magistraux et un mémoire.",
  "Construit avec du café froid et de la détermination.",
  "Code écrit à 2h du mat avant un partiel.",
  "Inspiré par trop de deadlines ratées de justesse.",
  "Side project d'un étudiant qui devrait réviser.",
];
const MASCOT_STATES = [
  { max: 20,  emoji: "😎", msg: "Tranquille. Tout est sous contrôle." },
  { max: 40,  emoji: "🧐", msg: "Quelques deadlines. Ça va aller." },
  { max: 60,  emoji: "😬", msg: "Ça commence à chauffer..." },
  { max: 80,  emoji: "😰", msg: "Grosse pression. Courage !" },
  { max: 100, emoji: "🤯", msg: "Mode survie activé. Dodo c'est fini." },
];

/* ── DOM ready ───────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  initScrollReveal();
  initCardTilt();
  setFooterQuote();
  initMascot();
  autoDismissFlash();
});

/* ── Toast ───────────────────────────────────────────────────── */
function showToast(message, type = "info", duration = 3200) {
  const container = document.getElementById("toastContainer") || createToastContainer();
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type] || "ℹ️"}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(12px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 320);
  }, duration);
}
function createToastContainer() {
  const c = document.createElement("div");
  c.id = "toastContainer";
  c.className = "toast-container";
  document.body.appendChild(c);
  return c;
}

/* ── Mark done (AJAX) ────────────────────────────────────────── */
function markDone(deadlineId, btn) {
  btn.disabled = true;
  btn.textContent = "...";
  fetch(`/deadlines/${deadlineId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "TERMINE" }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        showToast("Quête accomplie ! +XP", "success");
        triggerConfetti();
        const card = btn.closest(".quest-card");
        if (card) {
          card.style.transition = "all .5s ease";
          card.style.opacity = "0.45";
          card.style.transform = "scale(0.97)";
        }
        setTimeout(() => location.reload(), 1200);
      } else {
        showToast("Erreur lors de la mise à jour.", "error");
        btn.disabled = false;
        btn.textContent = "Terminer";
      }
    })
    .catch(() => { showToast("Erreur réseau.", "error"); btn.disabled = false; });
}

/* ── Auto dismiss flash ──────────────────────────────────────── */
function autoDismissFlash() {
  document.querySelectorAll(".flash").forEach((f) => {
    setTimeout(() => {
      f.style.transition = "all .4s ease";
      f.style.opacity = "0";
      f.style.transform = "translateX(40px)";
      setTimeout(() => f.remove(), 420);
    }, 4500);
  });
}

/* ── Scroll reveal ───────────────────────────────────────────── */
function initScrollReveal() {
  document.querySelectorAll(".quest-card, .stat-card, .card, .threat-card, .rec-item").forEach((el) => {
    el.classList.add("reveal");
  });
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add("visible"); io.unobserve(e.target); }
      });
    },
    { threshold: 0.08 }
  );
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
}

/* ── 3D card tilt ────────────────────────────────────────────── */
function initCardTilt() {
  document.querySelectorAll(".quest-card").forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const r = card.getBoundingClientRect();
      const x = ((e.clientX - r.left) / r.width - 0.5) * 10;
      const y = ((e.clientY - r.top)  / r.height - 0.5) * -10;
      card.style.transform = `perspective(800px) rotateX(${y}deg) rotateY(${x}deg) translateY(-2px)`;
    });
    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });
}

/* ── Mascot ──────────────────────────────────────────────────── */
function initMascot() {
  const face = document.getElementById("mascotFace");
  const bubble = document.getElementById("mascotBubble");
  if (!face || !bubble) return;
  const score = parseFloat(face.dataset.stress || "0");
  const state = MASCOT_STATES.find((s) => score <= s.max) || MASCOT_STATES[MASCOT_STATES.length - 1];
  face.textContent = state.emoji;
  bubble.textContent = state.msg;
  face.addEventListener("click", () => {
    const rand = MASCOT_STATES[Math.floor(Math.random() * MASCOT_STATES.length)];
    bubble.textContent = rand.msg;
    face.style.transform = "scale(1.25) rotate(-10deg)";
    setTimeout(() => (face.style.transform = ""), 300);
  });
}

/* ── Footer quote ────────────────────────────────────────────── */
function setFooterQuote() {
  const el = document.getElementById("footerQuote");
  if (!el) return;
  el.textContent = FOOTER_QUOTES[Math.floor(Math.random() * FOOTER_QUOTES.length)];
}

/* ── Blocus mode ─────────────────────────────────────────────── */
let timerInterval = null;
let secondsLeft = 25 * 60;
const TOTAL_SECONDS = 25 * 60;
const CIRCUMFERENCE = 2 * Math.PI * 62; // r=62

function toggleBlocus() {
  const overlay = document.getElementById("blocus-overlay");
  if (!overlay) return;
  const isHidden = overlay.classList.contains("hidden");
  overlay.classList.toggle("hidden");
  if (isHidden) {
    document.getElementById("blocus-quote").textContent =
      BLOCUS_QUOTES[Math.floor(Math.random() * BLOCUS_QUOTES.length)];
    updateTimerDisplay();
  } else {
    clearInterval(timerInterval);
    timerInterval = null;
    document.getElementById("timerStartBtn").textContent = "▶ Démarrer";
  }
}

function updateTimerDisplay() {
  const m = Math.floor(secondsLeft / 60).toString().padStart(2, "0");
  const s = (secondsLeft % 60).toString().padStart(2, "0");
  const el = document.getElementById("timer-display");
  if (el) el.textContent = `${m}:${s}`;
  updateTimerRing();
}

function updateTimerRing() {
  const ring = document.getElementById("timerRingFill");
  if (!ring) return;
  const progress = secondsLeft / TOTAL_SECONDS;
  const offset = CIRCUMFERENCE * (1 - progress);
  ring.style.strokeDasharray = CIRCUMFERENCE;
  ring.style.strokeDashoffset = offset;
  ring.style.stroke = progress > 0.5 ? "var(--cyan)" : progress > 0.25 ? "var(--gold)" : "var(--pink)";
}

function startTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
    document.getElementById("timerStartBtn").textContent = "▶ Reprendre";
    return;
  }
  document.getElementById("timerStartBtn").textContent = "⏸ Pause";
  timerInterval = setInterval(() => {
    if (secondsLeft <= 0) {
      clearInterval(timerInterval);
      timerInterval = null;
      document.getElementById("timerStartBtn").textContent = "▶ Démarrer";
      showToast("Pomodoro terminé ! Fais une pause de 5 min.", "success", 5000);
      triggerConfetti();
      return;
    }
    secondsLeft--;
    updateTimerDisplay();
  }, 1000);
}

function resetTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
  secondsLeft = TOTAL_SECONDS;
  document.getElementById("timerStartBtn").textContent = "▶ Démarrer";
  updateTimerDisplay();
}

/* ── Confetti ────────────────────────────────────────────────── */
function triggerConfetti() {
  const canvas = document.getElementById("confettiCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const colours = ["#00f5ff", "#ff2d78", "#9b59ff", "#00ff88", "#ffd700"];
  const particles = Array.from({ length: 120 }, () => ({
    x: Math.random() * canvas.width,
    y: -10,
    r: Math.random() * 7 + 3,
    d: Math.random() * 80 + 40,
    color: colours[Math.floor(Math.random() * colours.length)],
    tilt: Math.random() * 20 - 10,
    tiltAngle: 0,
    tiltSpeed: Math.random() * 0.1 + 0.05,
    speed: Math.random() * 3 + 2,
    opacity: 1,
  }));

  let frame = 0;
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach((p) => {
      p.tiltAngle += p.tiltSpeed;
      p.y += p.speed;
      p.tilt = Math.sin(p.tiltAngle) * 12;
      p.opacity = Math.max(0, 1 - p.y / canvas.height);
      ctx.globalAlpha = p.opacity;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.ellipse(p.x + p.tilt, p.y, p.r, p.r * 0.6, p.tilt, 0, Math.PI * 2);
      ctx.fill();
    });
    frame++;
    if (frame < 160) requestAnimationFrame(draw);
    else { ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.globalAlpha = 1; }
  }
  draw();
}
