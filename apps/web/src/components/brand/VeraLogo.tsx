import type { HTMLAttributes } from "react";

/** Cropped display of the V mark supplied for the VERA brand. */
export function VeraLogo(props: HTMLAttributes<HTMLSpanElement>) {
  const { className = "", ...rest } = props;
  return (
    <span className={`vera-logo-symbol ${className}`.trim()} aria-hidden="true" {...rest}>
      <img className="vera-logo-image" src="/vera-canva-logo.png" alt="" />
    </span>
  );
}
