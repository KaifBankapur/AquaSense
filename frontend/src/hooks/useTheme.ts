import { useEffect, useState } from "react";

const THEME_KEY = "aqua-theme";

export type Theme = "light" | "dark";

export function useTheme(): { theme: Theme; toggle: () => void } {
  // Black is the product default — a stored preference still wins.
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === "light" || stored === "dark") return stored;
    return "dark";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  return { theme, toggle: () => setTheme((t) => (t === "dark" ? "light" : "dark")) };
}