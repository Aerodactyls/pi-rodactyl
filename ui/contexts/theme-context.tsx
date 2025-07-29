"use client";

import { getPalette, Palette, palettes } from "@/lib/theme-palettes";
import {
  createContext,
  memo,
  useCallback,
  useContext,
  useEffect,
  useMemo,
} from "react";
import * as React from "react";
import useSWR from "swr";

export interface Theme {
  palette: Palette | { name: "system" };
  favoritePalettes?: string[];
  sortPalettesBy: "name" | "lightness" | "chroma" | "hue";
  sortPalettesAscending: boolean;
}

declare global {
  var __THEME__: any;
}

type ScriptProps = React.DetailedHTMLProps<
  React.ScriptHTMLAttributes<HTMLScriptElement>,
  HTMLScriptElement
>;

export interface UseThemeProps {
  /** List of all available palettes */
  palettes: Palette[];
  /** Current theme */
  theme: Theme;
  /** Name of the current palette */
  paletteName: string;
  /** Function to set the current palette by name */
  setPaletteName: (name: string) => Promise<void>;
  /** List of favorite palettes */
  favoritePalettes?: string[];
  /** Function to set a palette as favorite or remove it from favorites */
  setFavoritePalette: (name: string, isFavorite?: boolean) => Promise<void>;

  sortPalettesBy: "name" | "lightness" | "chroma" | "hue";

  setSortPalettesBy: (sortBy: "name" | "lightness" | "chroma" | "hue") => void;

  sortPalettesAscending: boolean;

  setSortPalettesAscending: (ascending?: boolean) => void;
}

export interface ThemeProviderProps extends React.PropsWithChildren {
  /** List of all available palettes */
  palettes?: Palette[];
  /** Disable all CSS transitions when switching themes */
  disableTransitionOnChange?: boolean;
  /** Key used to store theme setting in localStorage */
  storageKey?: string;
  /** Default theme */
  defaultTheme?: Theme;
  /** Nonce string to pass to the inline script and style elements for CSP headers */
  nonce?: string;
  /** Props to pass the inline script */
  scriptProps?: ScriptProps;
}

const MEDIA = "(prefers-color-scheme: dark)";
const ThemeContext = createContext<UseThemeProps | undefined>(undefined);

const DEFAULT_THEME: Theme = {
  palette: {
    name: "system",
  },
  favoritePalettes: ["light", "dark"],
  sortPalettesBy: "name",
  sortPalettesAscending: true,
};

function saveToLS(storageKey: string, value: string) {
  try {
    localStorage.setItem(storageKey, value);
  } catch {
    // Unsupported
  }
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

export function ThemeProvider(props: ThemeProviderProps) {
  const context = useContext(ThemeContext);

  // Ignore nested context providers, just passthrough children
  if (context) return <>{props.children}</>;
  return <Theme {...props} />;
}

async function fetchTheme(): Promise<Theme> {
  return resolveTheme({ overrides: {} });
}

function resolveTheme({
  base = DEFAULT_THEME,
  overrides,
}: {
  base?: Theme;
  overrides: Partial<Theme>;
}) {
  return {
    ...base,
    ...overrides,
  };
}

function Theme({
  disableTransitionOnChange = true,
  storageKey = "theme",
  defaultTheme = DEFAULT_THEME,
  children,
  nonce,
  scriptProps,
}: ThemeProviderProps) {
  const { data: theme, mutate } = useSWR("theme", fetchTheme, {
    fallbackData: resolveTheme({ overrides: globalThis.__THEME__ }),
    onSuccess: (theme) => {
      saveToLS(storageKey, JSON.stringify(theme));
    },
  });

  const mutateTheme = useCallback(
    async (themeUpdates: Partial<Theme>) => {
      const newTheme = resolveTheme({ base: theme, overrides: themeUpdates });

      mutate(newTheme, { revalidate: false });

      saveToLS(storageKey, JSON.stringify(newTheme));
    },
    [mutate, storageKey, theme],
  );

  const paletteName = theme.palette.name;

  const setPaletteName = useCallback(
    async (name: string) => {
      const newPalette =
        getPalette(name) ||
        (name === "system"
          ? ({ name: "system" } as Palette)
          : DEFAULT_THEME.palette);

      mutateTheme({ palette: newPalette });
    },
    [mutateTheme],
  );

  const applyPalette = useCallback(() => {
    if (!paletteName) return;

    if (disableTransitionOnChange) {
      disableAnimation(nonce)();
    }

    const resolved =
      paletteName === "system" ? (getSystemTheme() ?? "dark") : paletteName;
    const el = document.documentElement;

    // if (resolved) el.classList.add(resolved);

    // if (resolved === "light" || resolved === "dark") {
    //   el.style.colorScheme = resolved;
    // }

    const palette = getPalette(resolved);
    if (!palette) return;

    Object.entries(palette.colors).forEach(([k, v]) => {
      el.style.setProperty(k, v);
    });
  }, [disableTransitionOnChange, nonce, paletteName]);

  useEffect(() => {
    applyPalette();

    if (paletteName === "system") {
      const media = window.matchMedia(MEDIA);

      // Intentionally use deprecated listener methods to support iOS & old browsers
      media.addListener?.(applyPalette);
      media.addEventListener?.("change", applyPalette);

      return () => {
        media.removeListener?.(applyPalette);
        media.removeEventListener?.("change", applyPalette);
      };
    }
  }, [applyPalette, paletteName]);

  useEffect(() => {
    function handleStorage(e: StorageEvent) {
      if (e.key === storageKey) {
        mutate();
      }
    }
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [mutate, storageKey, applyPalette, theme]);

  const setFavoritePalette = useCallback(
    async (name: string, isFavorite: boolean = true) => {
      const current = theme.favoritePalettes || [];

      if (isFavorite === current.includes(name)) return;

      const newFavoritePalettes = isFavorite
        ? [...current, name]
        : current.filter((n) => n !== name);

      mutateTheme({ favoritePalettes: newFavoritePalettes });
    },
    [mutateTheme, theme],
  );

  const setSortPalettesBy = useCallback(
    (sortBy: "name" | "lightness" | "chroma" | "hue") => {
      if (sortBy === theme.sortPalettesBy) return;
      mutateTheme({ sortPalettesBy: sortBy });
    },
    [mutateTheme, theme.sortPalettesBy],
  );

  const setSortPalettesAscending = useCallback(
    (ascending: boolean = true) => {
      if (ascending === theme.sortPalettesAscending) return;
      mutateTheme({ sortPalettesAscending: ascending });
    },
    [mutateTheme, theme.sortPalettesAscending],
  );

  const providerValue = useMemo(
    () => ({
      theme,
      palettes,
      paletteName,
      setPaletteName,
      favoritePalettes: theme.favoritePalettes,
      setFavoritePalette,
      sortPalettesBy: theme.sortPalettesBy,
      setSortPalettesBy,
      sortPalettesAscending: theme.sortPalettesAscending,
      setSortPalettesAscending,
    }),
    [
      theme,
      paletteName,
      setPaletteName,
      setFavoritePalette,
      setSortPalettesBy,
      setSortPalettesAscending,
    ],
  );

  return (
    <ThemeContext.Provider value={providerValue}>
      <ThemeScript
        {...{
          defaultTheme,
          storageKey,
          nonce,
          scriptProps,
        }}
      />
      {children}
    </ThemeContext.Provider>
  );
}

function script(storageKey: string, defaultTheme: Theme) {
  const el = document.documentElement;

  function updateDOM(theme: string) {
    // el.classList.add(theme);

    if (theme === "light" || theme === "dark") {
      // el.style.colorScheme = theme;
    } else {
      const { colors }: { colors: Record<string, string> } =
        JSON.parse(localStorage.getItem(storageKey) || "{}").palette ||
        defaultTheme.palette;

      if (colors) {
        Object.entries(colors).forEach(([k, v]) => {
          el.style.setProperty(k, v);
        });
      }
    }
  }

  function getSystemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  const theme = JSON.parse(localStorage.getItem(storageKey) || "{}");

  globalThis.__THEME__ = theme;

  try {
    const themeName = theme.palette?.name || defaultTheme.palette.name;
    updateDOM(themeName === "system" ? getSystemTheme() : themeName);
  } catch {
    //
  }
}

const ThemeScript = memo(
  ({
    storageKey,
    defaultTheme,
    nonce,
    scriptProps,
  }: Omit<ThemeProviderProps, "children">) => {
    const scriptArgs = JSON.stringify([storageKey, defaultTheme]).slice(1, -1);

    return (
      <script
        {...scriptProps}
        suppressHydrationWarning
        nonce={typeof window === "undefined" ? nonce : ""}
        dangerouslySetInnerHTML={{
          __html: `(${script.toString()})(${scriptArgs})`,
        }}
      />
    );
  },
);

ThemeScript.displayName = "ThemeScript";

function disableAnimation(nonce?: string) {
  const css = document.createElement("style");
  if (nonce) css.setAttribute("nonce", nonce);
  css.appendChild(
    document.createTextNode(
      `*,*::before,*::after{-webkit-transition:none!important;-moz-transition:none!important;-o-transition:none!important;-ms-transition:none!important;transition:none!important}`,
    ),
  );
  document.head.appendChild(css);

  return () => {
    // Force restyle
    (() => window.getComputedStyle(document.body))();

    // Wait for next tick before removing
    setTimeout(() => {
      document.head.removeChild(css);
    }, 1);
  };
}

function getSystemTheme(e?: MediaQueryList | MediaQueryListEvent) {
  if (typeof window === "undefined") return undefined;
  if (!e) e = window.matchMedia(MEDIA);
  const isDark = e.matches;
  const systemTheme = isDark ? "dark" : "light";
  return systemTheme;
}
