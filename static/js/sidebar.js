let sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true";

function configurarSidebar() {
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const body = document.body;

  if (window.innerWidth >= 992) {
    body.classList.toggle("sidebar-collapsed", sidebarCollapsed);
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      if (window.innerWidth < 992) {
        body.classList.toggle("sidebar-show");

        const existingBackdrop = document.querySelector(".sidebar-backdrop");
        if (body.classList.contains("sidebar-show")) {
          if (!existingBackdrop) {
            const backdrop = document.createElement("div");
            backdrop.classList.add("sidebar-backdrop");
            backdrop.addEventListener("click", () => {
              body.classList.remove("sidebar-show");
              backdrop.remove();
            });
            body.appendChild(backdrop);
          }
        } else {
          if (existingBackdrop) existingBackdrop.remove();
        }
      } else {
        sidebarCollapsed = !sidebarCollapsed;
        body.classList.toggle("sidebar-collapsed", sidebarCollapsed);

        localStorage.setItem("sidebarCollapsed", sidebarCollapsed);
      }
    });
  }

  window.addEventListener("resize", () => {
    if (window.innerWidth >= 992) {
      const backdrop = document.querySelector(".sidebar-backdrop");
      if (backdrop) {
        body.classList.remove("sidebar-show");
        backdrop.remove();
      }

      body.classList.toggle("sidebar-collapsed", sidebarCollapsed);
    } else {
      body.classList.remove("sidebar-collapsed");
    }
  });
}

document.addEventListener("DOMContentLoaded", configurarSidebar);
