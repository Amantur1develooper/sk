document.addEventListener("DOMContentLoaded", () => {
  const hero = document.getElementById("aptHeroImg");
  const thumbs = document.getElementById("aptThumbs");
  const priceEl = document.getElementById("aptPrice");
  const perEl = document.getElementById("aptPricePer");
  const form = document.getElementById("aptForm");
  const statusLine = document.getElementById("aptStatusLine");

  if (priceEl && perEl) {
    const price = Number(priceEl.dataset.price || 0);
    const area = 42;
    if (price > 0 && area > 0) {
      const per = Math.round(price / area);
      perEl.textContent = new Intl.NumberFormat("ru-RU").format(per) + " сом/м²";
    }
  }

  if (thumbs && hero) {
    thumbs.addEventListener("click", (e) => {
      const btn = e.target.closest(".aptThumb");
      if (!btn) return;
      const src = btn.dataset.src;
      if (!src) return;

      hero.src = src;

      thumbs.querySelectorAll(".aptThumb").forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
    });
  }

  if (form && statusLine) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      statusLine.textContent = "Заявка отправлена. Мы свяжемся с вами в ближайшее время.";
      form.reset();
    });
  }
});



const fabMain = document.getElementById("fabMain");
const fabMenu = document.getElementById("fabMenu");

if (fabMain && fabMenu) {
  fabMain.addEventListener("click", () => {
    fabMenu.classList.toggle("active");
  });

  document.addEventListener("click", (e) => {
    if (!fabMain.contains(e.target) && !fabMenu.contains(e.target)) {
      fabMenu.classList.remove("active");
    }
  });
}
