"use client";

import { useEffect } from "react";

const REVEAL_SELECTOR = [
  ".vera-app #panel-content > *",
  ".vera-investigation-page main > div > *",
].join(",");
const COVER_REVEAL_SELECTOR = [
  ".vera-cover > section",
  ".vera-cover > footer",
  ".vera-cover-feature",
].join(",");

export function ScrollEffects() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;

    const revealed = new WeakSet<Element>();
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("vera-scroll-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0, rootMargin: "0px 0px 120px 0px" },
    );

    let scanFrame = 0;
    const scan = () => {
      if (scanFrame) return;
      scanFrame = window.requestAnimationFrame(() => {
        scanFrame = 0;
        document.querySelectorAll(`${REVEAL_SELECTOR},${COVER_REVEAL_SELECTOR}`).forEach((element) => {
          if (revealed.has(element)) return;
          revealed.add(element);
          const siblingIndex = Array.from(element.parentElement?.children ?? []).indexOf(element);
          const siblingCount = element.parentElement?.children.length ?? 1;
          const isCoverReveal = Boolean(element.closest(".vera-cover"));
          let style = siblingIndex % 2 === 0 ? "slide-left" : "slide-right";
          if (element.matches(".vera-cover-feature")) {
            style = siblingIndex < siblingCount / 2 ? "merge-left" : "merge-right";
          } else if (!isCoverReveal && siblingCount > 1) {
            style = siblingIndex < siblingCount / 2 ? "merge-left" : "merge-right";
          }

          element.setAttribute(isCoverReveal ? "data-vera-cover-reveal" : "data-vera-scroll-reveal", "");
          element.setAttribute("data-vera-reveal-style", style);
          const delay = isCoverReveal ? Math.max(0, siblingIndex % 4) * 70 : Math.max(0, siblingIndex % 3) * 45;
          (element as HTMLElement).style.setProperty("--vera-reveal-delay", `${delay}ms`);
          observer.observe(element);
        });
      });
    };

    scan();
    const mutations = new MutationObserver(scan);
    mutations.observe(document.body, { childList: true, subtree: true });

    return () => {
      mutations.disconnect();
      observer.disconnect();
      if (scanFrame) window.cancelAnimationFrame(scanFrame);
    };
  }, []);

  return null;
}
