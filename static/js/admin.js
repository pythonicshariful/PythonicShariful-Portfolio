/* Pythonic Shariful — admin JS: sidebar toggle, delete confirms, table search. */
(function () {
  "use strict";
  var toggle = document.getElementById("adminNavToggle");
  var sidebar = document.querySelector(".admin-sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      var open = sidebar.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
  // Confirm before any POST delete / destructive action.
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.getAttribute("data-confirm"))) e.preventDefault();
    });
  });
  // Live table search (filters rows/cards containing the query).
  document.querySelectorAll("[data-table-search]").forEach(function (input) {
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      document.querySelectorAll(".admin-table tbody tr, .msg-card").forEach(function (row) {
        row.style.display = !q || row.textContent.toLowerCase().indexOf(q) !== -1 ? "" : "none";
      });
    });
  });
})();
