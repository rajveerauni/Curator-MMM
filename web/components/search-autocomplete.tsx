"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";

import { useDebouncedValue } from "@/components/use-debounced-value";
import { filterSuggestions, type CompanySuggestion } from "@/lib/company-suggestions";

interface Props {
  value: string;
  onChange: (val: string) => void;
  onSelect?: (company: CompanySuggestion) => void;
  loading?: boolean;
  clearExportMessage: () => void;
}

export function SearchAutocomplete({
  value,
  onChange,
  onSelect,
  loading,
  clearExportMessage,
}: Props) {
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const debouncedValue = useDebouncedValue(value, 250);
  const suggestions = filterSuggestions(debouncedValue);
  const showNoResults = debouncedValue.trim().length > 0 && suggestions.length === 0;

  // Reset highlight when suggestions change
  useEffect(() => {
    setActiveIdx(-1);
  }, [debouncedValue]);

  const close = useCallback(() => {
    setOpen(false);
    setActiveIdx(-1);
  }, []);

  const select = useCallback(
    (s: CompanySuggestion) => {
      clearExportMessage();
      onChange(s.name);
      onSelect?.(s);
      close();
      // Blur so mobile keyboards dismiss
      inputRef.current?.blur();
    },
    [clearExportMessage, onChange, onSelect, close]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open) {
      if (e.key === "ArrowDown" && value.trim()) setOpen(true);
      return;
    }
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIdx((i) => Math.max(i - 1, -1));
        break;
      case "Enter":
        if (activeIdx >= 0 && suggestions[activeIdx]) {
          e.preventDefault();
          select(suggestions[activeIdx]);
        }
        break;
      case "Escape":
        close();
        break;
      default:
        break;
    }
  };

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        close();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [close]);

  const dropdownVisible = open && (suggestions.length > 0 || showNoResults);

  return (
    <div ref={containerRef} className="relative min-w-0 flex-1 max-w-md">
      {/* Search icon */}
      <span className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-outline">
        search
      </span>

      <input
        ref={inputRef}
        value={value}
        onChange={(e) => {
          clearExportMessage();
          onChange(e.target.value);
          setOpen(true);
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (value.trim()) setOpen(true);
        }}
        placeholder="Company or ticker…"
        autoComplete="off"
        spellCheck={false}
        className="w-full rounded-full border border-white/5 bg-surface-container-highest py-2 pl-10 pr-10 text-sm text-on-surface placeholder:text-outline focus:border-primary/30 focus:outline-none focus:ring-1 focus:ring-primary/40 transition-shadow"
        aria-label="Company search"
        aria-busy={loading}
        aria-autocomplete="list"
        aria-expanded={dropdownVisible}
        aria-haspopup="listbox"
        role="combobox"
      />

      {/* Spinner */}
      <AnimatePresence>
        {loading && (
          <motion.span
            key="spinner"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin rounded-full border-2 border-primary border-t-transparent"
            aria-hidden
          />
        )}
      </AnimatePresence>

      {/* Dropdown */}
      <AnimatePresence>
        {dropdownVisible && (
          <motion.ul
            key="dropdown"
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ duration: 0.13, ease: [0.25, 0.1, 0.25, 1] }}
            className="absolute left-0 right-0 top-[calc(100%+6px)] z-50 overflow-hidden rounded-xl border border-white/10 bg-surface-container py-1 shadow-xl shadow-black/40"
            role="listbox"
            aria-label="Company suggestions"
          >
            {showNoResults ? (
              <li className="px-4 py-3 text-sm text-outline">No results found</li>
            ) : (
              suggestions.map((s, i) => (
                <li
                  key={s.ticker}
                  role="option"
                  aria-selected={i === activeIdx}
                  onMouseDown={(e) => {
                    // Prevent input blur before click fires
                    e.preventDefault();
                    select(s);
                  }}
                  onMouseEnter={() => setActiveIdx(i)}
                  className={`flex cursor-pointer items-center justify-between gap-2 px-4 py-2.5 text-sm transition-colors ${
                    i === activeIdx
                      ? "bg-primary/10 text-primary"
                      : "text-on-surface hover:bg-white/5"
                  }`}
                >
                  <span className="min-w-0 truncate font-medium">{s.name}</span>
                  <span className="shrink-0 rounded-md bg-surface-container-highest px-1.5 py-0.5 text-[10px] font-bold text-outline">
                    {s.ticker}
                  </span>
                </li>
              ))
            )}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
