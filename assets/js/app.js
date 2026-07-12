// Exercise 1 Min — landing interactions.
// Progressive enhancement only: the page is fully usable with JS disabled
// (the reveal styles apply only when the <html class="js"> flag is set, which
// an inline <head> script sets before first paint).
(function () {
  "use strict";

  document.documentElement.classList.add("js"); // idempotent with the head flag

  // Current year in the footer (falls back to the hardcoded year in the HTML).
  var yearEl = document.querySelector("[data-year]");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  // Category filter tabs — show one category's cards at a time (or all). Set up before the
  // reveal logic below so it works even when that path early-returns (reduced motion / no IO).
  var tabs = document.querySelector(".cat-tabs");
  if (tabs) {
    var pills = Array.prototype.slice.call(tabs.querySelectorAll(".cat-pill"));
    var catCards = Array.prototype.slice.call(
      document.querySelectorAll(".exercise-card[data-cat]")
    );
    var status = document.getElementById("cat-status");
    var applyFilter = function (cat) {
      var shown = 0;
      catCards.forEach(function (card) {
        var show = cat === "all" || card.getAttribute("data-cat") === cat;
        card.classList.toggle("cat-hide", !show);
        // A card revealed by the filter may never have scrolled into view, so make sure
        // its reveal transition doesn't leave it invisible.
        if (show) {
          card.classList.add("is-visible");
          shown++;
        }
      });
      return shown;
    };
    tabs.addEventListener("click", function (e) {
      var pill = e.target.closest && e.target.closest(".cat-pill");
      if (!pill || !tabs.contains(pill)) return;
      pills.forEach(function (p) {
        var active = p === pill;
        p.classList.toggle("is-active", active);
        p.setAttribute("aria-pressed", active ? "true" : "false");
      });
      var shown = applyFilter(pill.getAttribute("data-cat"));
      if (status) {
        var label = (pill.firstChild && pill.firstChild.textContent || pill.textContent).trim();
        status.textContent =
          pill.getAttribute("data-cat") === "all"
            ? "Showing all " + shown + " exercises."
            : "Showing " + shown + " " + label + " exercises.";
      }
    });
  }

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
