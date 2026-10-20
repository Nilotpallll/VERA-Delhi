/** Decorative market signal used behind the product UI; contains no data. */
export function FinanceBackdrop() {
  const marketPath = "M830 420L905 385L965 410L1035 330L1100 350L1170 270L1235 300L1305 205L1370 230L1445 150";

  return (
    <div className="vera-finance-backdrop" aria-hidden="true">
      <svg viewBox="0 0 1440 900" preserveAspectRatio="xMaxYMid slice">
        <g className="vera-market-grid">
          <path d="M860 130H1440M860 230H1440M860 330H1440M860 430H1440M860 530H1440" />
          <path d="M960 100V560M1080 100V560M1200 100V560M1320 100V560" />
        </g>
        <path className="vera-market-line" d={marketPath} pathLength="900" />
        <path className="vera-market-line-live" d={marketPath} pathLength="900" />
        <path className="vera-market-scan" d="M1080 100V560" />
        <g className="vera-market-points">
          <circle cx="965" cy="410" r="4" />
          <circle cx="1100" cy="350" r="4" />
          <circle cx="1235" cy="300" r="4" />
          <circle cx="1370" cy="230" r="4" />
        </g>
        <circle className="vera-market-ticker" r="5">
          <animateMotion dur="13s" repeatCount="indefinite" path={marketPath} />
        </circle>
        <circle className="vera-market-ticker vera-market-ticker-secondary" r="3">
          <animateMotion dur="13s" begin="-6.5s" repeatCount="indefinite" path={marketPath} />
        </circle>
        <g className="vera-evidence-thread">
          <path className="vera-evidence-thread-base" d="M115 590C160 548 190 510 238 514S302 458 342 445S405 370 472 350" />
          <path className="vera-evidence-thread-live" d="M115 590C160 548 190 510 238 514S302 458 342 445S405 370 472 350" pathLength="400" />
          <g className="vera-evidence-thread-points">
            <circle cx="115" cy="590" r="3" />
            <circle cx="238" cy="514" r="3.5" />
            <circle cx="342" cy="445" r="3" />
            <circle cx="472" cy="350" r="4" />
          </g>
          <circle className="vera-evidence-thread-ticker" r="3.5">
            <animateMotion dur="20s" repeatCount="indefinite" path="M115 590C160 548 190 510 238 514S302 458 342 445S405 370 472 350" />
          </circle>
        </g>
        <path className="vera-market-baseline" d="M0 760H1440" />
      </svg>
    </div>
  );
}
