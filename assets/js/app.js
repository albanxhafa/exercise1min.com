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

  // Keep the public catalog aligned with the mobile app's current routine data.
  // Timed movements are 10 seconds, except the 15-second mobility stretch.
  var floorExerciseIds = new Set([
    "bridges",
    "flutter-kicks",
    "crunches",
    "heel-taps",
    "climbers",
    "plank-hold",
    "shoulder-taps",
    "prone-reverse-fly",
    "w-extensions",
    "air-bike-crunches",
    "scissors",
    "crunch-kicks",
    "plank-rotations",
    "reverse-angels",
    "raised-leg-circles",
    "plank-leg-raises"
  ]);
  var allExerciseCards = Array.prototype.slice.call(
    document.querySelectorAll(".exercise-card[data-cat]")
  );
  allExerciseCards.forEach(function (card) {
    var isFloor = floorExerciseIds.has(card.id);
    card.setAttribute("data-position", isFloor ? "floor" : "desk");
    var duration = card.querySelector(".illo-dur");
    if (duration && duration.textContent.indexOf("sec") !== -1) {
      duration.textContent = card.id === "stretches" ? "15 sec" : "10 sec";
    }
  });

  // Category filter tabs — show one category's cards at a time (or all). Set up before the
  // reveal logic below so it works even when that path early-returns (reduced motion / no IO).
  var tabs = document.querySelector(".cat-tabs");
  if (tabs) {
    var pills = Array.prototype.slice.call(tabs.querySelectorAll(".cat-pill"));
    var catCards = allExerciseCards;
    var status = document.getElementById("cat-status");
    var applyFilter = function (cat) {
      var shown = 0;
      catCards.forEach(function (card) {
        var show =
          cat === "all" ||
          (cat === "desk" && card.getAttribute("data-position") === "desk") ||
          card.getAttribute("data-cat") === cat;
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
    var activePill = tabs.querySelector(".cat-pill.is-active");
    if (activePill) {
      var initialShown = applyFilter(activePill.getAttribute("data-cat"));
      if (status) status.textContent = "Showing " + initialShown + " desk-ready exercises.";
    }
  }

  // A small interactive sample of the app's standing-first routine generator.
  // There is deliberately no countdown: "one minute" is a promise, not a timer.
  var demoList = document.getElementById("demo-moves");
  var floorToggle = document.getElementById("include-floor");
  var shuffleButton = document.getElementById("shuffle-routine");
  var demoNote = document.getElementById("demo-note");
  var renderRoutine = function () {
    if (!demoList) return;
    var includeFloor = Boolean(floorToggle && floorToggle.checked);
    var available = allExerciseCards.filter(function (card) {
      return includeFloor || card.getAttribute("data-position") === "desk";
    });
    var chosen = [];
    var lastCategory = "";

    while (chosen.length < 5 && available.length) {
      var varied = available.filter(function (card) {
        return card.getAttribute("data-cat") !== lastCategory;
      });
      var candidates = varied.length ? varied : available;
      var card = candidates[Math.floor(Math.random() * candidates.length)];
      chosen.push(card);
      lastCategory = card.getAttribute("data-cat");
      available.splice(available.indexOf(card), 1);
    }

    chosen.sort(function (a, b) {
      return Number(a.getAttribute("data-position") === "floor") -
        Number(b.getAttribute("data-position") === "floor");
    });
    demoList.replaceChildren();
    chosen.forEach(function (card, index) {
      var item = document.createElement("li");
      var number = document.createElement("span");
      number.className = "move-num";
      number.textContent = String(index + 1).padStart(2, "0");
      var name = document.createElement("strong");
      name.textContent = card.querySelector("h3").textContent;
      var measure = document.createElement("small");
      measure.textContent = card.querySelector(".illo-dur").textContent;
      item.append(number, name, measure);
      demoList.appendChild(item);
    });

    if (demoNote) {
      demoNote.textContent = includeFloor
        ? "Floor moves are grouped at the end to minimize posture changes."
        : "Standing and mobility moves only.";
    }
  };
  if (shuffleButton) shuffleButton.addEventListener("click", renderRoutine);
  if (floorToggle) floorToggle.addEventListener("change", renderRoutine);
  renderRoutine();

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
