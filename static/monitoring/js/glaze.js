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

  function syncPresentationContext() {
    const width = window.innerWidth;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const reducedTransparency = window.matchMedia("(prefers-reduced-transparency: reduce)").matches;
    const increasedContrast = window.matchMedia("(prefers-contrast: more)").matches;
    const forcedColors = window.matchMedia("(forced-colors: active)").matches;
    const largeText = window.matchMedia("(min-resolution: 0.001dpcm)").matches
      && parseFloat(getComputedStyle(root).fontSize || "16") >= 20;

    root.dataset.glazeUi = "1.5.1";
    root.dataset.glazeUiTarget = "1.5.1";
    root.dataset.glazeUiStatus = "source-adoption-candidate";
    root.dataset.glazeAuthority = "presentation-only";
    root.dataset.glazePaneMode = width < 600 ? "single" : width < 1024 ? "stacked" : "split";
    root.dataset.glazeControlDensity = largeText ? "comfortable" : width < 600 ? "compact" : "standard";
    root.dataset.glazeMaterial = (reducedTransparency || increasedContrast || forcedColors)
      ? "solid-accessible"
      : "glaze";
    root.dataset.glazeMotion = reducedMotion ? "reduced" : "standard";
    root.dataset.glazeLargeText = largeText ? "true" : "false";
  }

  const contextQueries = [
    window.matchMedia("(prefers-reduced-motion: reduce)"),
    window.matchMedia("(prefers-reduced-transparency: reduce)"),
    window.matchMedia("(prefers-contrast: more)"),
    window.matchMedia("(forced-colors: active)"),
  ];

  syncPresentationContext();
  window.addEventListener("resize", syncPresentationContext);
  for (const query of contextQueries) query.addEventListener("change", syncPresentationContext);

  let current = readPreference();
  applyPreference(current);

  button?.addEventListener("click", () => {
    current = values[(values.indexOf(current) + 1) % values.length];
    applyPreference(current, true);
  });
})();
