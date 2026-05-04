import { Search, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { searchFoods } from "../api/foods";
import Badge from "./ui/Badge.jsx";

function cookingBadgeVariant(state) {
  if (state === "cooked") return "teal";
  if (state === "raw") return "blue";
  return null;
}

export default function FoodSearch({ onSelect, clearAfterSelect = false }) {
  const containerRef = useRef(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setIsLoading(false);
      setActiveIndex(-1);
      return undefined;
    }

    const timerId = window.setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await searchFoods({ q: query.trim(), limit: 10 });
        setResults(data.items || []);
        setIsOpen(true);
        setActiveIndex((data.items || []).length ? 0 : -1);
      } catch {
        setResults([]);
        setIsOpen(true);
        setActiveIndex(-1);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => window.clearTimeout(timerId);
  }, [query]);

  function handleSelect(food) {
    onSelect(food);
    if (clearAfterSelect) {
      setQuery("");
      setResults([]);
    } else {
      setQuery(food.name);
    }
    setIsOpen(false);
    setActiveIndex(-1);
  }

  function clearSearch() {
    setQuery("");
    setResults([]);
    setIsOpen(false);
    setActiveIndex(-1);
  }

  function handleKeyDown(event) {
    if (!isOpen || !results.length) {
      if (event.key === "ArrowDown" && results.length) {
        setIsOpen(true);
      }
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((current) => (current + 1) % results.length);
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((current) => (current <= 0 ? results.length - 1 : current - 1));
    }

    if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      handleSelect(results[activeIndex]);
    }

    if (event.key === "Escape") {
      setIsOpen(false);
      setActiveIndex(-1);
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      <label className="block">
        <span className="mb-1 block text-sm font-medium text-gray-700">Search foods</span>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden="true" />
          <input
            className="min-h-11 w-full rounded-xl border border-gray-200 bg-white px-10 pr-10 text-base text-gray-800 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500"
            placeholder="Type at least 2 characters"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setIsOpen(true);
            }}
            onFocus={() => {
              if (results.length || query.trim().length >= 2) {
                setIsOpen(true);
              }
            }}
            onKeyDown={handleKeyDown}
          />
          {query ? (
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 transition hover:text-gray-600"
              onClick={clearSearch}
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      </label>

      {isOpen ? (
        <div className="absolute left-0 right-0 z-30 mt-2 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg">
          {isLoading ? <div className="px-4 py-3 text-sm text-gray-500">Searching…</div> : null}
          {!isLoading && query.trim().length >= 2 && !results.length ? (
            <div className="px-4 py-3 text-sm text-gray-500">No foods found for that search yet.</div>
          ) : null}
          {!isLoading && results.length ? (
            <ul className="max-h-72 overflow-y-auto py-1">
              {results.map((food, index) => {
                const badgeVariant = cookingBadgeVariant(food.cooking_state);
                const isActive = index === activeIndex;
                return (
                  <li key={food.id}>
                    <button
                      type="button"
                      className={`flex w-full items-start justify-between gap-3 px-4 py-3 text-left transition ${isActive ? "bg-teal-50" : "hover:bg-gray-50"}`}
                      onMouseEnter={() => setActiveIndex(index)}
                      onClick={() => handleSelect(food)}
                    >
                      <div>
                        <div className="font-medium text-gray-800">{food.name}</div>
                        <div className="text-sm text-gray-500">
                          {food.display_calories || food.calories || 0} kcal · {food.display_protein_g || food.protein_g || 0}g protein
                        </div>
                      </div>
                      {badgeVariant ? <Badge label={food.cooking_state} variant={badgeVariant} /> : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
