import React, { createContext, useContext, useEffect } from 'react';
import type { ThemeMode } from '../types';

interface ThemeContextType {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  isDark: boolean;
}

const STORAGE_KEY = 'credirisk-theme';

const applyThemeToDom = () => {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.classList.add('dark');
  root.setAttribute('data-theme', 'dark');
  root.style.colorScheme = 'dark';

  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', '#0B1220');
  }
};

const ThemeContext = createContext<ThemeContextType>({
  theme: 'dark',
  setTheme: () => {},
  isDark: true,
});

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    applyThemeToDom();
    try {
      localStorage.setItem(STORAGE_KEY, 'dark');
    } catch {
      // Storage access might be restricted
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ theme: 'dark', setTheme: () => {}, isDark: true }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
