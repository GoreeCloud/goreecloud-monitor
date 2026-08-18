(() => {
  const STORAGE_KEY = "goreecloud-monitor-appearance";
  const root = document.documentElement;
  const button = document.querySelector("[data-appearance-toggle]");
  const label = button?.querySelector("[data-appearance-label]");
  const values = ["system", "light", "dark"];

  function readPreference() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return values.includes(value) ? value : "system";
    } catch (_) {
      return "system";
    }
  }

  function applyPreference(value, persist = false) {
    if (value === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", value);

    if (persist) {
      try {
        if (value === "system") localStorage.removeItem(STORAGE_KEY);
        else localStorage.setItem(STORAGE_KEY, value);
      } catch (_) {
        // Appearance remains functional even when browser storage is unavailable.
      }
    }

    const visible = value.charAt(0).toUpperCase() + value.slice(1);
    if (button) button.setAttribute("aria-label", `Appearance: ${visible}. Activate to change.`);
    if (label) label.textContent = visible;
  }

  let current = readPreference();
  applyPreference(current);

  button?.addEventListener("click", () => {
    current = values[(values.indexOf(current) + 1) % values.length];
    applyPreference(current, true);
  });
})();
