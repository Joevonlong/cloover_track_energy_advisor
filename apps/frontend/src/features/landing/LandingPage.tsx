import { useState } from "react";
import { ArrowRight, BadgeEuro, BatteryCharging, Check, MapPinned, SunMedium } from "lucide-react";

function HeimswendeLogo() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 22 22"
      fill="none"
      aria-hidden="true"
    >
      {/* Blue rounded-square container, like Pactum */}
      <rect width="22" height="22" rx="5" fill="#2f6fed" />
      {/* White house mark — negative space inside the square */}
      <path
        d="M11 4.5L18.5 10.5V18H14V13H8V18H3.5V10.5L11 4.5Z"
        fill="white"
      />
    </svg>
  );
}

interface LandingPageProps {
  onStart: () => void;
}

export default function LandingPage({ onStart }: LandingPageProps) {
  const [exiting, setExiting] = useState(false);

  function handleStart() {
    if (exiting) return;
    setExiting(true);
    setTimeout(onStart, 480);
  }

  return (
    <div className={`landing-root${exiting ? " landing-root--exiting" : ""}`}>
      <div className="landing-progress" aria-hidden="true" />
      <nav className="landing-nav">
        <div className="landing-brand">
          <HeimswendeLogo />
          <span className="landing-brand-name">Heimwende</span>
        </div>
        <div className="landing-nav-note">Solar, storage, heating, and financing</div>
      </nav>

      <main className="landing-main">
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-copy">
            <p className="landing-eyebrow">
              Berlin energy retrofit cockpit
            </p>
            <h1 className="landing-headline" id="landing-title">
              Your home energy plan, ready in minutes.
            </h1>
            <p className="landing-sub">
              Heimwende checks your roof, household demand, permits, subsidies,
              and financing options in one guided flow.
            </p>
            <div className="landing-actions">
              <button className="landing-cta" onClick={handleStart} type="button">
                Start Heimwende
                <ArrowRight size={18} strokeWidth={2.4} aria-hidden="true" />
              </button>
              <span className="landing-assurance">
                <Check size={16} strokeWidth={2.5} aria-hidden="true" />
                No sales call before the first estimate
              </span>
            </div>

            <dl className="landing-metrics" aria-label="Planning highlights">
              <div>
                <dt>4 layers</dt>
                <dd>Solar, storage, heating, mobility</dd>
              </div>
              <div>
                <dt>15 min</dt>
                <dd>From address to first proposal</dd>
              </div>
              <div>
                <dt>1 plan</dt>
                <dd>Service, subsidy, and financing view</dd>
              </div>
            </dl>
          </div>

          <div className="landing-media" aria-label="Energy plan preview">
            <div className="landing-image-frame">
              <img
                src="/pic.avif"
                alt="House with solar panels, an electric car, and homeowners outside"
                className="landing-img"
                draggable={false}
              />
              <div className="landing-image-shade" aria-hidden="true" />
            </div>

            <div className="landing-floating-card landing-floating-card--top">
              <div className="landing-card-icon">
                <MapPinned size={18} strokeWidth={2.3} aria-hidden="true" />
              </div>
              <div>
                <span>Roof scan</span>
                <strong>8.6 kWp potential</strong>
              </div>
            </div>

            <div className="landing-caption">
              <Check size={16} strokeWidth={2.4} aria-hidden="true" />
              Subsidy, permit, and payback checks included
            </div>
          </div>
        </section>

        <section className="landing-workflow" aria-label="How Heimwende works">
          <article>
            <SunMedium size={20} strokeWidth={2.2} aria-hidden="true" />
            <span>01</span>
            <h2>Find roof yield</h2>
            <p>Start with the address and refine the roof area on the map.</p>
          </article>
          <article>
            <BatteryCharging size={20} strokeWidth={2.2} aria-hidden="true" />
            <span>02</span>
            <h2>Compare bundles</h2>
            <p>Balance solar, battery, heat pump, EV charging, and tariffs.</p>
          </article>
          <article>
            <BadgeEuro size={20} strokeWidth={2.2} aria-hidden="true" />
            <span>03</span>
            <h2>Make it financeable</h2>
            <p>See subsidy checks, permit hints, and monthly payment ranges.</p>
          </article>
        </section>
      </main>
    </div>
  );
}
