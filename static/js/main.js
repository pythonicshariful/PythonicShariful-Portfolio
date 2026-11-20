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

  // Scroll reveal (IntersectionObserver, ~300ms, capped stagger)
  var revealEls = document.querySelectorAll(".reveal");
  if (reduced || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.classList.add("visible"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry, i) {
        if (entry.isIntersecting) {
          entry.target.style.transitionDelay = Math.min(i * 40, 120) + "ms";
          entry.target.classList.add("visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  // FAQ: single-open accordion — opening one closes the others.
  var faqItems = document.querySelectorAll(".faq-item");
  faqItems.forEach(function (item) {
    item.addEventListener("toggle", function () {
      if (item.open) {
        faqItems.forEach(function (other) { if (other !== item) other.open = false; });
      }
    });
  });

  // Hero terminal typing animation — lines type out one by one, then loop.
  // Reduced motion: leave the static HTML lines as they are.
  var term = document.getElementById("hero-term");
  if (term && !reduced) {
    var termLines = [
      { prefix: "", text: "$ python stock-monitor.py", cls: "term-cmd" },
      { prefix: '<span class="term-ok">\u2713</span> ', text: "Session ready \u2014 fresh sticky proxy", cls: "" },
      { prefix: '<span class="term-ok">\u2713</span> ', text: "Microsoft Store \u2014 200 OK \u00b7 checking\u2026", cls: "" },
      { prefix: '<span class="term-ok">\u2713</span> ', text: "Price changed \u2014 alert sent to Telegram", cls: "" }
    ];
    var cursor = document.createElement("span");
    cursor.className = "term-cursor";
    var lineIdx = 0, charIdx = 0, curSpan = null;
    function typeTick() {
      if (lineIdx >= termLines.length) {
        var prompt = document.createElement("p");
        prompt.innerHTML = '<span class="term-cmd">$</span> ';
        prompt.appendChild(cursor);
        term.appendChild(prompt);
        setTimeout(function () { term.innerHTML = ""; lineIdx = 0; charIdx = 0; typeTick(); }, 5000);
        return;
      }
      var line = termLines[lineIdx];
      if (charIdx === 0) {
        var curP = document.createElement("p");
        if (line.prefix) curP.innerHTML = line.prefix;
        curSpan = document.createElement("span");
        if (line.cls) curSpan.className = line.cls;
        curP.appendChild(curSpan);
        curP.appendChild(cursor);
        term.appendChild(curP);
      }
      curSpan.textContent += line.text.charAt(charIdx);
      charIdx++;
      if (charIdx < line.text.length) {
        setTimeout(typeTick, 26);
      } else {
        lineIdx++; charIdx = 0;
        setTimeout(typeTick, lineIdx === 1 ? 500 : 380);
      }
    }
    term.innerHTML = "";
    setTimeout(typeTick, 600);
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
