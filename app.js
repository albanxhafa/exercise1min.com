// Exercise 1 Min / Ushtrohu 1 Minutë — landing interactions.
// Progressive enhancement only: the page is fully usable with JS disabled
// (the reveal styles apply only when the <html class="js"> flag is set, which
// an inline <head> script sets before first paint).
(function () {
  "use strict";

  document.documentElement.classList.add("js"); // idempotent with the head flag

  // Current year in the footer (falls back to the hardcoded year in the HTML).
  var yearEl = document.querySelector("[data-year]");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  var reveals = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  var prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function revealAll() {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  }

  if (!("IntersectionObserver" in window) || prefersReduced) {
    revealAll();
    return;
  }

  // Reveal anything already in (or near) the viewport right away, so above-the-fold
  // content never waits on the async observer callback. This also guarantees the
  // full page shows in tall/headless render contexts.
  var vh = window.innerHeight || document.documentElement.clientHeight;
  reveals.forEach(function (el) {
    var top = el.getBoundingClientRect().top;
    if (top < vh * 0.95) el.classList.add("is-visible");
  });

  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );

  reveals.forEach(function (el) {
    if (!el.classList.contains("is-visible")) io.observe(el);
  });
})();
