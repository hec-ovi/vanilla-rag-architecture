import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
  theme: Theme;
  isDark: boolean;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  initTheme: () => void;
}

const getSystemTheme = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
};

const applyTheme = (isDark: boolean) => {
  if (typeof document === 'undefined') return;
  
  const root = document.documentElement;
  if (isDark) {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      isDark: getSystemTheme(),
      
      setTheme: (theme) => {
        const isDark = theme === 'system' ? getSystemTheme() : theme === 'dark';
        set({ theme, isDark });
        applyTheme(isDark);
      },
      
      toggleTheme: () => {
        const newIsDark = !get().isDark;
        set({ theme: newIsDark ? 'dark' : 'light', isDark: newIsDark });
        applyTheme(newIsDark);
      },
      
      initTheme: () => {
        const { theme } = get();
        const isDark = theme === 'system' ? getSystemTheme() : theme === 'dark';
        set({ isDark });
        applyTheme(isDark);
        
        // Listen for system theme changes
        if (typeof window !== 'undefined') {
          const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
          mediaQuery.addEventListener('change', (e) => {
            if (get().theme === 'system') {
              set({ isDark: e.matches });
              applyTheme(e.matches);
            }
          });
        }
      },
    }),
    {
      name: 'vanilla-rag-theme',
    }
  )
);
