document.addEventListener("DOMContentLoaded", () => {
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const smoothScrollTo = (target) => {
    if (!target) return;
    target.scrollIntoView({ behavior: prefersReduced ? "auto" : "smooth", block: "start" });
  };

  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      const href = a.getAttribute("href");
      if (!href || href === "#") return; 
      const el = document.querySelector(href);
      if (!el) return;

      e.preventDefault();
      closeMenu();
      smoothScrollTo(el);
    });
  });

  const navbar = document.querySelector(".navbar");
  const onScrollNavbar = () => {
    if (!navbar) return;
    if (window.scrollY > 50) {
      navbar.style.background = "rgba(0,0,0,0.85)";
      navbar.style.backdropFilter = "blur(10px)";
    } else {
      navbar.style.background = "transparent";
      navbar.style.backdropFilter = "none";
    }
  };
  window.addEventListener("scroll", onScrollNavbar, { passive: true });
  onScrollNavbar();

  const burger = document.querySelector(".burger");
  const navList = document.querySelector(".navbar .list");
  const overlay = document.querySelector(".nav-overlay");

  const lockBody = (lock) => {
    document.documentElement.style.overflow = lock ? "hidden" : "";
    document.body.style.overflow = lock ? "hidden" : "";
  };

  function openMenu() {
    if (!navList) return;
    navList.classList.add("active");
    if (overlay) overlay.classList.add("active");
    lockBody(true);
    if (burger) burger.classList.add("active");
  }

  function closeMenu() {
    if (!navList) return;
    navList.classList.remove("active");
    if (overlay) overlay.classList.remove("active");
    lockBody(false);
    if (burger) burger.classList.remove("active");
  }

  if (burger && navList) {
    burger.addEventListener("click", () => {
      navList.classList.contains("active") ? closeMenu() : openMenu();
    });
  }

  if (overlay) {
    overlay.addEventListener("click", closeMenu);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });

  if (navList) {
    navList.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => closeMenu());
    });
  }

  const categoryButtons = document.querySelectorAll(".categories button");
  const cards = document.querySelectorAll(".card");

  categoryButtons.forEach((button) => {
    button.addEventListener("click", () => {
      categoryButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");

      const filter = button.textContent.trim();

      cards.forEach((card) => {
        const statusEl = card.querySelector(".info span");
        const status = statusEl ? statusEl.textContent.trim() : "";

        if (filter === "Все" || filter === status) {
          card.style.display = "block";
        } else {
          card.style.display = "none";
        }
      });

      if (!prefersReduced && window.gsap) {
        gsap.fromTo(
          ".cards .card",
          { opacity: 0, y: 18 },
          { opacity: 1, y: 0, duration: 0.4, stagger: 0.05, clearProps: "transform" }
        );
      }
    });
  });

  const choiceButtons = document.querySelectorAll(".choices button");
  choiceButtons.forEach((button) => {
    button.addEventListener("click", () => {
      choiceButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");
    });
  });

  const counters = document.querySelectorAll(".countSums h1");
  const parseTarget = (txt) => {
    const cleaned = txt.replace(/\s/g, "").replace("+", "");
    const n = parseInt(cleaned, 10);
    return Number.isFinite(n) ? n : 0;
  };

  const animateCounter = (el) => {
    const target = parseTarget(el.textContent);
    const hasPlus = el.textContent.includes("+");
    const duration = prefersReduced ? 0 : 1200;
    const start = 0;
    const startTime = performance.now();

    const tick = (now) => {
      const t = Math.min(1, (now - startTime) / duration);
      const eased = 1 - Math.pow(1 - t, 3); 
      const value = Math.floor(start + (target - start) * eased);
      el.textContent = value + (hasPlus ? "+" : "");
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = target + (hasPlus ? "+" : "");
    };

    requestAnimationFrame(tick);
  };

  if (counters.length) {
    const counterObserver = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach((c) => counterObserver.observe(c));
  }

  if (!prefersReduced && window.gsap) {
    gsap.registerPlugin(ScrollTrigger);

    gsap.from(".banner .info h1", { y: 24, opacity: 0, duration: 0.9, ease: "power3.out" });
    gsap.from(".banner .info p", { y: 20, opacity: 0, duration: 0.8, delay: 0.15, ease: "power3.out" });
    gsap.from(".banner .info button", { y: 16, opacity: 0, duration: 0.7, delay: 0.25, ease: "power3.out" });

    // About image + text
    gsap.from(".aboutUs .aboutText img", {
      scrollTrigger: { trigger: ".aboutUs", start: "top 75%" },
      scale: 0.96,
      opacity: 0,
      duration: 0.9,
      ease: "power2.out"
    });
    gsap.from(".aboutUs .aboutText h2", {
      scrollTrigger: { trigger: ".aboutUs", start: "top 75%" },
      y: 18,
      opacity: 0,
      duration: 0.8,
      delay: 0.05,
      ease: "power2.out"
    });

    // Cards stagger
    gsap.from(".buildings .card", {
      scrollTrigger: { trigger: ".buildings .cards", start: "top 80%" },
      y: 24,
      opacity: 0,
      duration: 0.7,
      stagger: 0.12,
      ease: "power2.out"
    });

    // Counts block
    gsap.from(".counts h1", {
      scrollTrigger: { trigger: ".counts", start: "top 80%" },
      y: 18,
      opacity: 0,
      duration: 0.8,
      ease: "power2.out"
    });

    gsap.from(".counts .countSums > div", {
      scrollTrigger: { trigger: ".counts", start: "top 80%" },
      y: 18,
      opacity: 0,
      duration: 0.7,
      stagger: 0.12,
      ease: "power2.out"
    });

    // View360
    gsap.from(".view360 h1", {
      scrollTrigger: { trigger: ".view360", start: "top 80%" },
      y: 18,
      opacity: 0,
      duration: 0.8,
      ease: "power2.out"
    });
    gsap.from(".view360 button", {
      scrollTrigger: { trigger: ".view360", start: "top 80%" },
      y: 16,
      opacity: 0,
      duration: 0.75,
      delay: 0.05,
      ease: "power2.out"
    });
  }
});


const priceEl = document.getElementById("calcPrice");
const downEl = document.getElementById("calcDown");
const monthsEl = document.getElementById("calcMonths");
const markupEl = document.getElementById("calcMarkup");
const feeEl = document.getElementById("calcFee");
const markupOnRestEl = document.getElementById("calcMarkupOnRest");
const btnEl = document.getElementById("calcBtn");

const resRest = document.getElementById("resRest");
const resMarkupSum = document.getElementById("resMarkupSum");
const resTotal = document.getElementById("resTotal");
const resMonthly = document.getElementById("resMonthly");
const resMarkupPctOfPrice = document.getElementById("resMarkupPctOfPrice");
const resOverpay = document.getElementById("resOverpay");

const fmt = (n) => {
  const v = Math.round(n);
  return v.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " сом";
};

const calc = () => {
  const price = Number(priceEl.value || 0);
  const down = Number(downEl.value || 0);
  const months = Math.max(1, Number(monthsEl.value || 1));
  const markupPct = Math.max(0, Number(markupEl.value || 0));
  const fee = Math.max(0, Number(feeEl.value || 0));
  const markupOnRest = markupOnRestEl.checked;

  if (price <= 0) {
    alert("Введите цену объекта");
    return;
  }

  const safeDown = Math.min(down, price);
  const rest = Math.max(0, price - safeDown);

  const baseForMarkup = markupOnRest ? rest : price;
  const markupSum = baseForMarkup * (markupPct / 100);

  const total = price + markupSum + fee;               
  const financed = total - safeDown;                  
  const monthly = financed / months;

  const overpay = total - price;                       
  const markupPctOfPrice = (markupSum / price) * 100;  

  resRest.textContent = fmt(rest);
  resMarkupSum.textContent = fmt(markupSum);
  resTotal.textContent = fmt(total);
  resMonthly.textContent = fmt(monthly);
  resMarkupPctOfPrice.textContent = markupPctOfPrice.toFixed(2) + "%";
  resOverpay.textContent = fmt(overpay);

  if (window.gsap && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    gsap.fromTo(
      ".installmentBox .results",
      { y: 10, opacity: 0.6 },
      { y: 0, opacity: 1, duration: 0.35, ease: "power2.out" }
    );
  }
};

if (btnEl) btnEl.addEventListener("click", calc);

[priceEl, downEl, monthsEl, markupEl, feeEl, markupOnRestEl].forEach((el) => {
  if (!el) return;
  el.addEventListener("input", () => {
    if (Number(priceEl.value || 0) > 0) calc();
  });
});

const $view360btn = document.querySelector('.view360btn')

$view360btn.addEventListener('click', e => {
  e.preventDefault()

  window.open('https://kuula.co/edit/hCzrW/collection/7DbCt', target="_blank")
})

const preloader = document.getElementById("preloader");
document.body.classList.add("is-loading");

const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const hidePreloader = () => {
  if (!preloader) return;

  if (window.gsap && !prefersReduced) {
    gsap.to(preloader, {
      opacity: 0,
      duration: 0.6,
      ease: "power2.out",
      onComplete: () => {
        preloader.classList.add("is-hidden");
        document.body.classList.remove("is-loading");
      }
    });
  } else {
    preloader.classList.add("is-hidden");
    document.body.classList.remove("is-loading");
  }
};

window.addEventListener("load", () => {
  setTimeout(hidePreloader, 1000);
});


const form = document.getElementById("contactForm");
const statusEl = document.getElementById("formStatus");

if (form) {
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const btn = form.querySelector("button");
    btn.disabled = true;
    statusEl.textContent = "Отправка...";

    setTimeout(() => {
      statusEl.style.color = "#6dff8b";
      statusEl.textContent = "Спасибо! Мы свяжемся с вами в ближайшее время.";
      form.reset();
      btn.disabled = false;
    }, 1200);
  });
}

/* =========================
   INSTALLMENT CONFIG
========================= */

const projectConfig = {
  eco: {
    markup: 10,
    months: 24,
    fee: 0,
    markupOnRest: true
  },
  city: {
    markup: 15,
    months: 18,
    fee: 30000,
    markupOnRest: false
  },
  premium: {
    markup: 8,
    months: 36,
    fee: 50000,
    markupOnRest: true
  }
};

const projectSelect = document.getElementById("calcProject");
const markupInput = document.getElementById("calcMarkup");
const monthsInput = document.getElementById("calcMonths");
const feeInput = document.getElementById("calcFee");
const markupOnRestCheckbox = document.getElementById("calcMarkupOnRest");

if (projectSelect) {
  projectSelect.addEventListener("change", () => {
    const config = projectConfig[projectSelect.value];

    markupInput.value = config.markup;
    monthsInput.value = config.months;
    feeInput.value = config.fee;
    markupOnRestCheckbox.checked = config.markupOnRest;
  });
}

const calcBtn = document.getElementById("calcBtn");

if (calcBtn) {
  calcBtn.addEventListener("click", () => {

    const price = parseFloat(document.getElementById("calcPrice").value) || 0;
    const down = parseFloat(document.getElementById("calcDown").value) || 0;
    const months = parseFloat(document.getElementById("calcMonths").value) || 1;
    const markup = parseFloat(document.getElementById("calcMarkup").value) || 0;
    const fee = parseFloat(document.getElementById("calcFee").value) || 0;
    const markupOnRest = document.getElementById("calcMarkupOnRest").checked;

    if (price <= 0) {
      alert("Введите корректную цену объекта");
      return;
    }

    const rest = Math.max(price - down, 0);

    const baseForMarkup = markupOnRest ? rest : price;
    const markupSum = baseForMarkup * (markup / 100);

    const total = price + markupSum + fee;
    const overpay = markupSum + fee;
    const monthly = months > 0 ? (rest + markupSum + fee) / months : 0;

    const percentOfPrice = (overpay / price) * 100;

    const format = (num) => 
      new Intl.NumberFormat("ru-RU").format(Math.round(num));

    document.getElementById("resRest").innerText = format(rest) + " сом";
    document.getElementById("resMarkupSum").innerText = format(markupSum) + " сом";
    document.getElementById("resTotal").innerText = format(total) + " сом";
    document.getElementById("resMonthly").innerText = format(monthly) + " сом";
    document.getElementById("resMarkupPctOfPrice").innerText = percentOfPrice.toFixed(2) + "%";
    document.getElementById("resOverpay").innerText = format(overpay) + " сом";
  });
}