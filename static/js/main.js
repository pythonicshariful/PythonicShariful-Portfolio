/* Pythonic Shariful — public site JS: mobile nav, scroll reveal, stats count-up.
   No 3D hero (light theme). Content is visible with JS disabled: reveal
   states are gated on the .js class added in base.html. */
(function () {
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Mobile nav
  var toggle = document.getElementById("navToggle");
  var nav = document.getElementById("siteNav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") { nav.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
    });
  }

  // Scroll reveal (IntersectionObserver, ~450ms)
  var revealEls = document.querySelectorAll(".reveal");
  if (reduced || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.classList.add("visible"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry, i) {
        if (entry.isIntersecting) {
          entry.target.style.transitionDelay = Math.min(i * 60, 240) + "ms";
          entry.target.classList.add("visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  // Stats count-up: 0 -> data-count over ~2s when scrolled into view.
  // Reduced motion: final value immediately.
  var statNums = document.querySelectorAll(".stat-num[data-count]");
  function setFinal(el) { el.textContent = el.getAttribute("data-count"); }
  if (statNums.length) {
    if (reduced || !("IntersectionObserver" in window)) {
      statNums.forEach(setFinal);
    } else {
      var sio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          sio.unobserve(el);
          var target = parseInt(el.getAttribute("data-count"), 10) || 0;
          var start = null;
          var duration = 2000;
          el.textContent = "0";
          (function tick(ts) {
            if (start === null) start = ts;
            var p = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(target * eased);
            if (p < 1) requestAnimationFrame(tick);
            else el.textContent = target;
          })(performance.now());
        });
      }, { threshold: 0.4 });
      statNums.forEach(function (el) { sio.observe(el); });
    }
  }
})();
