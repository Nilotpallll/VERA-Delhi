"use client";

import { useEffect } from "react";

const REVEAL_SELECTOR = [
  ".vera-cover > section",
  ".vera-cover > footer",
  ".vera-cover-feature",
  ".vera-app #panel-content > *",
  ".vera-app #panel-content section",
  ".vera-app #panel-content article",
  ".vera-app #panel-content table",
  ".vera-app #panel-content .vera-risk-metric",
  ".vera-investigation-page main > div > *",
  ".vera-investigation-page main section",
  ".vera-investigation-page main article",
  ".vera-investigation-page main table",
  ".vera-investigation-page main .vera-glass",
  ".vera-investigation-page main [data-motion-item]",
  "#vera-results .vera-results-grid > *",
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
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" },
    );

    const scan = () => {
      document.querySelectorAll(REVEAL_SELECTOR).forEach((element) => {
        if (revealed.has(element)) return;
        revealed.add(element);
        const siblingIndex = Array.from(element.parentElement?.children ?? []).indexOf(element);
        const siblingCount = element.parentElement?.children.length ?? 1;
        let style = siblingIndex % 2 === 0 ? "slide-left" : "slide-right";

        if (element.matches(".vera-risk-metric")) style = "pop";
        else if (element.matches(".vera-cover-feature, #panel-content article, #vera-results .vera-results-grid > *")) {
          style = siblingIndex < siblingCount / 2 ? "merge-left" : "merge-right";
        } else if (element.matches("#panel-content table")) style = "wipe";

        element.setAttribute("data-vera-scroll-reveal", "");
        element.setAttribute("data-vera-reveal-style", style);
        (element as HTMLElement).style.setProperty("--vera-reveal-delay", `${Math.max(0, siblingIndex % 4) * 70}ms`);
        observer.observe(element);
      });
    };

    scan();
    const mutations = new MutationObserver(scan);
    mutations.observe(document.body, { childList: true, subtree: true });

    return () => {
      mutations.disconnect();
      observer.disconnect();
    };
  }, []);

  return null;
}
