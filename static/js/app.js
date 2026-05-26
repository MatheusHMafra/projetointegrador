axios.defaults.headers.post["Content-Type"] = "application/json";
axios.defaults.headers.common["Accept"] = "application/json";

document.addEventListener("DOMContentLoaded", function () {
  setupThemeManager();

  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]'),
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

function setupThemeManager() {
  const themeToggle = document.getElementById("theme-toggle");
  const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");

  const applyTheme = (theme) => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    updateThemeToggleIcon(theme);

    document.dispatchEvent(
      new CustomEvent("themeChanged", { detail: { theme: theme } }),
    );
  };

  const currentTheme = localStorage.getItem("theme");

  if (currentTheme) {
    applyTheme(currentTheme);
  } else {
    applyTheme("dark");
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      const currentTheme = document.documentElement.getAttribute("data-theme");
      const newTheme = currentTheme === "light" ? "dark" : "light";
      applyTheme(newTheme);
    });
  }
}

function updateThemeToggleIcon(theme) {
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.innerHTML = "";
    const icon = document.createElement("i");
    icon.className = theme === "light" ? "fas fa-moon" : "fas fa-sun";
    themeToggle.appendChild(icon);
    themeToggle.title =
      theme === "light" ? "Mudar para tema escuro" : "Mudar para tema claro";
  }
}

function showNotification(message, type = "success") {
  const notification = document.getElementById("notification");
  if (!notification) {
    console.warn("Elemento de notificação #notification não encontrado.");
    return;
  }
  notification.textContent = message;

  notification.className = `alert alert-${type} notification-popup`;
  notification.style.display = "block";
  notification.style.opacity = 1;

  setTimeout(() => {
    notification.style.opacity = 0;

    setTimeout(() => {
      notification.style.display = "none";
    }, 300);
  }, 3000);
}

function toggleLoading(show = true) {
  const spinner = document.getElementById("loading-spinner");
  if (!spinner) {
    console.warn(
      "Elemento de loading spinner #loading-spinner não encontrado.",
    );
    return;
  }
  spinner.style.display = show ? "flex" : "none";
}

function inicializarDropdownsTabela(containerId) {
  const selector = containerId
    ? `#${containerId} .table-actions-toggle`
    : ".table-actions-toggle";

  const dropdownButtons = document.querySelectorAll(selector);
  dropdownButtons.forEach((btn) => {
    const existingInstance = bootstrap.Dropdown.getInstance(btn);
    if (existingInstance) {
      existingInstance.destroy();
    }

    new bootstrap.Dropdown(btn, {
      popperConfig(defaultConfig) {
        return {
          ...defaultConfig,
          strategy: "fixed",
        };
      },
    });
  });
}

document.addEventListener("themeChanged", (event) => {
  const newTheme = event.detail.theme;

  if (typeof atualizarTemaGraficos === "function") {
    atualizarTemaGraficos(newTheme);
  }
});
