import { useEffect, useMemo, useRef, type ReactNode, type RefObject } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import "./scroll-reveal.css";

/**
 * React Bits — ScrollReveal.
 * Words fade, un-blur and de-rotate as the block scrolls into view.
 *
 * Adapted for AquaSense:
 * - TypeScript props; string/number children are split into `.word` spans
 *   while element children are rendered as-is (the vendor source discarded them)
 * - animations run inside `gsap.matchMedia()` scoped to this instance, so
 *   unmounting reverts *only* its own triggers. The vendor source called
 *   `ScrollTrigger.getAll().kill()`, which would tear down every other scroll
 *   trigger on the page.
 * - honours `prefers-reduced-motion`: with reduced motion requested no
 *   triggers are created at all, leaving the text in its plain readable state
 *   instead of parked at `baseOpacity` / `blurStrength` mid-scrub
 * - `aria-label` keeps the full sentence available to screen readers
 *   now that the text is broken across spans
 */
gsap.registerPlugin(ScrollTrigger);

const ScrollReveal = ({
  children,
  scrollContainerRef,
  enableBlur = true,
  baseOpacity = 0.1,
  baseRotation = 3,
  blurStrength = 4,
  containerClassName = "",
  textClassName = "",
  rotationEnd = "bottom bottom",
  wordAnimationEnd = "bottom bottom",
}: {
  children: ReactNode;
  scrollContainerRef?: RefObject<HTMLElement>;
  enableBlur?: boolean;
  baseOpacity?: number;
  baseRotation?: number;
  blurStrength?: number;
  containerClassName?: string;
  textClassName?: string;
  rotationEnd?: string;
  wordAnimationEnd?: string;
}) => {
  const containerRef = useRef<HTMLHeadingElement>(null);

  // Only plain text is split into per-word spans. The vendor source coerced
  // every non-string child to "" and rendered that, which silently discarded
  // element children; they are now rendered as-is, per the documented contract.
  const isText = typeof children === "string" || typeof children === "number";

  const content = useMemo(() => {
    if (!isText) return children;
    return String(children)
      .split(/(\s+)/)
      .map((word, index) =>
        // keep the whitespace separators as plain text between the word spans
        /^\s+$/.test(word) ? (
          word
        ) : (
          <span className="word" key={index}>
            {word}
          </span>
        ),
      );
  }, [children, isText]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || typeof window === "undefined") return;

    const scroller =
      scrollContainerRef && scrollContainerRef.current ? scrollContainerRef.current : window;

    // `mm` owns every animation/trigger created inside the callback, so
    // `mm.revert()` on cleanup leaves other ScrollReveal instances untouched.
    const mm = gsap.matchMedia();

    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.fromTo(
        el,
        { transformOrigin: "0% 50%", rotate: baseRotation },
        {
          ease: "none",
          rotate: 0,
          scrollTrigger: {
            trigger: el,
            scroller,
            start: "top bottom",
            end: rotationEnd,
            scrub: true,
          },
        },
      );

      const wordElements = el.querySelectorAll(".word");

      gsap.fromTo(
        wordElements,
        { opacity: baseOpacity, willChange: "opacity" },
        {
          ease: "none",
          opacity: 1,
          stagger: 0.05,
          scrollTrigger: {
            trigger: el,
            scroller,
            start: "top bottom-=20%",
            end: wordAnimationEnd,
            scrub: true,
          },
        },
      );

      if (enableBlur) {
        gsap.fromTo(
          wordElements,
          { filter: `blur(${blurStrength}px)` },
          {
            ease: "none",
            filter: "blur(0px)",
            stagger: 0.05,
            scrollTrigger: {
              trigger: el,
              scroller,
              start: "top bottom-=20%",
              end: wordAnimationEnd,
              scrub: true,
            },
          },
        );
      }
    });

    return () => mm.revert();
  }, [
    scrollContainerRef,
    enableBlur,
    baseRotation,
    baseOpacity,
    rotationEnd,
    wordAnimationEnd,
    blurStrength,
  ]);

  const label = isText ? String(children) : undefined;

  return (
    <h2 ref={containerRef} className={`scroll-reveal ${containerClassName}`.trim()} aria-label={label}>
      <p className={`scroll-reveal-text ${textClassName}`.trim()}>{content}</p>
    </h2>
  );
};

export default ScrollReveal;
export { ScrollReveal };
