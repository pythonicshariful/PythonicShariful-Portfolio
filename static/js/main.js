/* Pythonic Shariful — public site JS: mobile nav, scroll reveal, 3D hero. */
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

  // Scroll reveal (IntersectionObserver, 300-450ms)
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

  // 3D hero — Three.js via CDN. Graceful fallback: if THREE is missing
  // (CDN offline) the page simply shows the static hero, which is complete.
  function initHero3D() {
    var canvas = document.getElementById("hero3d");
    if (!canvas || typeof THREE === "undefined" || reduced) return;
    try {
      var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100);
      camera.position.z = 9;

      var torus = new THREE.Mesh(
        new THREE.TorusGeometry(2.6, 0.55, 16, 90),
        new THREE.MeshBasicMaterial({ color: 0x22c55e, wireframe: true, transparent: true, opacity: 0.55 })
      );
      torus.position.x = 3.4;
      scene.add(torus);

      // Floating particles + "code" particles
      var count = 260;
      var pos = new Float32Array(count * 3);
      for (var i = 0; i < count * 3; i++) pos[i] = (Math.random() - 0.5) * 16;
      var geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      var points = new THREE.Points(geo, new THREE.PointsMaterial({ color: 0x94a3b8, size: 0.06, transparent: true, opacity: 0.8 }));
      scene.add(points);

      function resize() {
        var w = canvas.parentElement.clientWidth, h = canvas.parentElement.clientHeight;
        renderer.setSize(w, h, false);
        camera.aspect = w / Math.max(h, 1);
        camera.updateProjectionMatrix();
      }
      resize();
      window.addEventListener("resize", resize);

      var paused = false;
      document.addEventListener("visibilitychange", function () { paused = document.hidden; });
      var t = 0;
      (function animate() {
        requestAnimationFrame(animate);
        if (paused) return;
        t += 0.004;
        torus.rotation.x = t * 0.6;
        torus.rotation.y = t * 0.9;
        points.rotation.y = t * 0.12;
        renderer.render(scene, camera);
      })();
    } catch (e) {
      // Never break the page if WebGL fails.
      if (window.console) console.warn("3D hero unavailable:", e);
    }
  }
  // Three.js script tag is deferred; wait for it, with a short timeout.
  if (document.getElementById("hero3d")) {
    if (typeof THREE !== "undefined") initHero3D();
    else window.addEventListener("load", function () { setTimeout(initHero3D, 300); });
  }
})();
