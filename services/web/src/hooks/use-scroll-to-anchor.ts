import { useEffect } from "react";

export function useScrollToAnchor() {
  useEffect(() => {
    const scrollToElement = (hash: string) => {
      if (!hash) return;
      const element = document.querySelector(hash);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    };

    // Handle initial hash on page load
    const hash = window.location.hash;
    if (hash) {
      // Delay to ensure DOM is ready
      setTimeout(() => scrollToElement(hash), 100);
    }

    // Listen for hash changes (back/forward button and direct URL hash changes)
    const handleHashChange = () => {
      scrollToElement(window.location.hash);
    };

    // Listen for popstate events (back button, etc)
    const handlePopState = () => {
      scrollToElement(window.location.hash);
    };

    window.addEventListener("hashchange", handleHashChange);
    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("hashchange", handleHashChange);
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);
}
