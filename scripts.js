// Global FitSphere frontend interactions

document.addEventListener("DOMContentLoaded", () => {
  highlightActiveNavLink();
  attachFormHandlers();
  enableSmoothScroll();
});

// Highlight current page in nav based on filename
function highlightActiveNavLink() {
  const path = window.location.pathname;
  const current = path.substring(path.lastIndexOf("/") + 1) || "index.html";

  document.querySelectorAll(".main-nav a").forEach((link) => {
    const href = link.getAttribute("href");
    if (!href) return;
    const hrefFile = href.split("?")[0].split("#")[0];
    if (hrefFile === current) {
      link.classList.add("active-link");
    }
  });
}

// Attach simple handlers to common forms (login, register, contact, payments)
function attachFormHandlers() {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();

      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      // Simple demo feedback – replace with real API calls later
      showToast("Form submitted (frontend demo only)");
    });
  });
}

// Smooth scroll for same-page anchor links
function enableSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      const targetId = this.getAttribute("href");
      if (!targetId || targetId === "#") return;
      const target = document.querySelector(targetId);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

// Simple toast notification
function showToast(message) {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("visible");
  setTimeout(() => toast.classList.remove("visible"), 2500);
}
