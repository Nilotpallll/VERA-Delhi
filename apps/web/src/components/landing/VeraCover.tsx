"use client";

import { ArrowDown, ArrowRight, Check, Moon, ShieldAlert, Sparkles, Sun } from "lucide-react";
import { Volume2, VolumeX } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Locale, translations } from "@/lib/i18n";
import { FinanceBackdrop } from "@/components/shell/FinanceBackdrop";
import { ScrollEffects } from "@/components/shell/ScrollEffects";
import { VeraLogo } from "@/components/brand/VeraLogo";

export type VeraTheme = "light" | "dark";

interface SubtitleCue {
  start: number;
  end: number;
  text: string;
}

const COVER_SUBTITLES: Record<Locale, SubtitleCue[]> = {
  en: [
    { start: 0.0, end: 2.5, text: "Intelligently screening every claim." },
    { start: 2.5, end: 5.0, text: "From the moment evidence is submitted," },
    { start: 5.0, end: 7.4, text: "VERA instantly maps identity," },
    { start: 7.4, end: 11.5, text: "Surfacing subtle risk signals for proper screening." },
    { start: 11.5, end: 16.0, text: "Before you invest, let VERA test." },
    { start: 16.0, end: 20.0, text: "Verification and Evidence Based Risk Analyser" },
  ],
  hi: [
    { start: 0.0, end: 2.5, text: "हर दावे की बुद्धिमानी से जांच।" },
    { start: 2.5, end: 5.0, text: "सबूत प्रस्तुत होते ही," },
    { start: 5.0, end: 7.4, text: "वेरा तुरंत पहचान का विश्लेषण करता है," },
    { start: 7.4, end: 11.5, text: "और सटीक जांच के लिए सूक्ष्म जोखिम संकेतों को उजागर करता है।" },
    { start: 11.5, end: 16.0, text: "निवेश करने से पहले, वेरा से जांचें।" },
    { start: 16.0, end: 20.0, text: "वेरिफिकेशन एंड एविडेंस बेस्ड रिस्क एनालाइज़र" },
  ],
};

export function VeraCover({
  locale,
  theme,
  onLocaleChange,
  onThemeToggle,
  onEnter,
}: {
  locale: Locale;
  theme: VeraTheme;
  onLocaleChange: () => void;
  onThemeToggle: () => void;
  onEnter: () => void;
}) {
  const t = translations[locale];
  const videoRef = useRef<HTMLVideoElement>(null);
  const loopTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isMuted, setIsMuted] = useState(true);
  const [videoCurrentTime, setVideoCurrentTime] = useState(0);
  const [showSubtitles, setShowSubtitles] = useState(true);

  const isVisibleRef = useRef(true);

  // Auto-play on mount and auto-pause when scrolled down out of view, resume when scrolled back up
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            isVisibleRef.current = true;
            video.play().catch(() => {});
          } else {
            isVisibleRef.current = false;
            video.pause();
          }
        });
      },
      {
        threshold: 0.2,
      }
    );

    observer.observe(video);

    return () => {
      observer.disconnect();
      if (loopTimeoutRef.current) {
        clearTimeout(loopTimeoutRef.current);
      }
    };
  }, []);

  const handleVideoEnded = () => {
    if (loopTimeoutRef.current) {
      clearTimeout(loopTimeoutRef.current);
    }
    // 3 seconds delay before restarting the video loop
    loopTimeoutRef.current = setTimeout(() => {
      const video = videoRef.current;
      if (video) {
        video.currentTime = 0;
        if (isVisibleRef.current) {
          video.play().catch(() => {});
        }
      }
    }, 3000);
  };

  const activeCue = COVER_SUBTITLES[locale]?.find(
    (cue) => videoCurrentTime >= cue.start && videoCurrentTime < cue.end
  );

  const toggleVideoSound = async () => {
    const video = videoRef.current;
    if (!video) return;
    if (isMuted) {
      video.muted = false;
      if (video.ended || (video.duration && video.currentTime >= video.duration - 0.2)) {
        if (loopTimeoutRef.current) clearTimeout(loopTimeoutRef.current);
        video.currentTime = 0;
      }
      try {
        await video.play();
        setIsMuted(false);
      } catch {
        video.muted = true;
      }
    } else {
      video.muted = true;
      setIsMuted(true);
    }
  };

  const handleOpenVeronica = (query?: string) => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("vera:open-veronica", {
          detail: { query, language: locale },
        })
      );
    }
  };

  const features = [
    { number: "01", title: t.coverFeatureScreen, body: t.coverFeatureScreenBody },
    { number: "02", title: t.coverFeatureVideo, body: t.coverFeatureVideoBody },
    { number: "03", title: t.coverFeatureCase, body: t.coverFeatureCaseBody },
    {
      number: "04",
      title: t.coverFeatureVeronica,
      body: t.coverFeatureVeronicaBody,
      isVeronica: true,
    },
  ];
  const limits = [t.coverLimitOne, t.coverLimitTwo, t.coverLimitThree];

  return (
    <div className="vera-cover">
      <ScrollEffects />
      <FinanceBackdrop />
      <header className="vera-cover-nav">
        <a className="vera-cover-brand" href="#cover-top" aria-label="VERA home">
          <span className="vera-cover-monogram"><VeraLogo className="vera-logo-symbol" /></span>
          <span className="vera-cover-lockup">
            <span className="vera-cover-wordmark">
              <span className="sr-only">VERA</span>
              <span className="vera-wordmark-frame" aria-hidden="true">
                <img src="/vera-wordmark-reference.jpeg" alt="VERA" width={120} height={32} />
              </span>
            </span>
            <span className="vera-cover-fullform">{t.brandDescriptor}</span>
          </span>
        </a>
        <nav className="vera-cover-nav-actions" aria-label={t.coverExploreLink}>
          <a className="vera-cover-nav-link" href="#cover-story">{t.coverExploreLink}</a>
          <button
            type="button"
            className="vera-cover-control vera-cover-veronica-btn"
            onClick={() => handleOpenVeronica()}
            aria-label={t.coverVeronicaBtn}
            title={t.coverVeronicaBtn}
          >
            <span className="vera-veronica-sparkle-dot" />
            <VeraLogo className="vera-cover-veronica-logo" />
            <span>{t.coverVeronicaBtn}</span>
          </button>
          <button
            type="button"
            id="btn-cover-theme"
            className="vera-cover-control"
            onClick={onThemeToggle}
            aria-label={t.themeToggle}
            title={t.themeToggle}
            aria-pressed={theme === "dark"}
          >
            {theme === "light" ? <Moon aria-hidden="true" /> : <Sun aria-hidden="true" />}
            <span>{theme === "light" ? t.darkMode : t.lightMode}</span>
          </button>
          <button
            type="button"
            id="btn-cover-lang"
            className="vera-cover-control vera-cover-language"
            onClick={onLocaleChange}
            aria-label={t.languageSwitch}
            aria-pressed={locale === "hi"}
          >
            {locale === "en" ? "हिंदी" : "English"}
          </button>
          <button
            type="button"
            id="btn-cover-enter"
            className="vera-cover-nav-enter-btn"
            onClick={onEnter}
            aria-label={t.coverEnter}
          >
            <span>{t.coverEnter}</span>
            <ArrowRight aria-hidden="true" className="w-3.5 h-3.5" />
          </button>
        </nav>
      </header>

      <section className="vera-cover-hero" id="cover-top" aria-labelledby="cover-title">
        <div className="vera-cover-copy">
          <p className="vera-cover-eyebrow"><span className="vera-cover-eyebrow-mark" aria-hidden="true" />{t.coverEyebrow}</p>
          <h1 id="cover-title" className="vera-cover-title">
            <span>{t.coverTitleLead}</span>
            <em>{t.coverTitleAccent}</em>
          </h1>
          <p className="vera-cover-description">{t.coverDescription}</p>
          <div className="vera-cover-cta-row">
            <button
              type="button"
              id="btn-hero-launch-scanner"
              className="vera-cover-cta vera-cover-enter-hero-cta"
              onClick={onEnter}
            >
              <span>{t.coverEnterHero}</span>
              <ArrowRight aria-hidden="true" />
            </button>
            <button
              type="button"
              id="btn-hero-veronica"
              className="vera-cover-cta vera-cover-veronica-hero-cta"
              onClick={() => handleOpenVeronica()}
            >
              <VeraLogo className="vera-cover-veronica-hero-logo" />
              <span>{t.coverVeronicaHeroCta}</span>
            </button>
            <a className="vera-cover-cta vera-cover-explore" href="#cover-story">
              {t.coverExplore}<ArrowDown aria-hidden="true" />
            </a>
          </div>
          <p className="vera-cover-footnote">{t.brandTagline}</p>
        </div>

        <div className="vera-cover-art vera-cover-video-frame" role="group" aria-label={t.coverArtLabel}>
          <video
            ref={videoRef}
            className="vera-cover-video"
            src="/vera-cover.mp4"
            poster="/vera-cover-poster.jpg"
            autoPlay
            muted={isMuted}
            playsInline
            preload="auto"
            aria-hidden="true"
            tabIndex={-1}
            onTimeUpdate={() => {
              if (videoRef.current) {
                setVideoCurrentTime(videoRef.current.currentTime);
              }
            }}
            onEnded={handleVideoEnded}
          />

          {/* Synchronized Subtitles Overlay */}
          {showSubtitles && activeCue && (
            <div className="vera-video-subtitle-overlay" aria-live="polite">
              <span className="vera-video-subtitle-badge">CC</span>
              <p className="vera-video-subtitle-text">{activeCue.text}</p>
            </div>
          )}

          {/* Subtitles Toggle (Bottom Left) */}
          <button
            className={`vera-cover-cc-toggle ${showSubtitles ? "is-active" : ""}`}
            type="button"
            onClick={() => setShowSubtitles((s) => !s)}
            aria-label={showSubtitles ? (locale === "hi" ? "उपशीर्षक बंद करें" : "Disable subtitles") : (locale === "hi" ? "उपशीर्षक चालू करें" : "Enable subtitles")}
            title={showSubtitles ? (locale === "hi" ? "उपशीर्षक बंद करें" : "Disable subtitles") : (locale === "hi" ? "उपशीर्षक चालू करें" : "Enable subtitles")}
          >
            <span className="vera-cc-tag">CC</span>
            <span>{showSubtitles ? (locale === "hi" ? "उपशीर्षक चालू" : "Subtitles On") : (locale === "hi" ? "उपशीर्षक बंद" : "Subtitles Off")}</span>
          </button>

          {/* Sound Toggle (Bottom Right) */}
          <button
            className="vera-cover-audio-toggle"
            type="button"
            onClick={toggleVideoSound}
            aria-label={isMuted ? t.coverSoundOn : t.coverSoundOff}
            aria-pressed={!isMuted}
            title={isMuted ? t.coverSoundOn : t.coverSoundOff}
          >
            {isMuted ? <VolumeX aria-hidden="true" /> : <Volume2 aria-hidden="true" />}
            <span>{isMuted ? t.coverSoundOn : t.coverSoundOff}</span>
          </button>
        </div>

        <a className="vera-cover-scroll" href="#cover-story" aria-label={t.coverExplore}>
          <span>SCROLL TO EXPLORE</span><ArrowDown aria-hidden="true" />
        </a>
      </section>

      <section className="vera-cover-story" id="cover-story" aria-labelledby="cover-story-title">
        <div className="vera-cover-section-intro">
          <p className="vera-cover-eyebrow"><span className="vera-cover-eyebrow-mark" aria-hidden="true" />{t.coverStoryEyebrow}</p>
          <h2 id="cover-story-title">{t.coverStoryTitle}</h2>
          <div className="vera-cover-story-aside">
            <p>{t.coverStoryDescription}</p>
            <article className="vera-demo-analysis" aria-label={t.coverDemoAria}>
              <div className="vera-demo-heading">
                <span className="vera-demo-brand">VERA <i>/</i> {t.coverDemoLabel}</span>
                <span className="vera-demo-badge">{t.coverDemoBadge}</span>
              </div>
              <div className="vera-demo-message">
                <span className="vera-demo-message-label">{t.coverDemoSample}</span>
                <p>“{t.coverDemoMessage}”</p>
              </div>
              <div className="vera-demo-cues-label">{t.coverDemoEvidenceLabel}</div>
              <div className="vera-demo-checks" role="list" aria-label={t.coverDemoEvidenceLabel}>
                <div className="vera-demo-check vera-demo-check-one" role="listitem">
                  <span className="vera-demo-index">01</span>
                  <strong>{t.coverDemoSender}</strong><small>{t.coverDemoSenderHint}</small>
                </div>
                <div className="vera-demo-check vera-demo-check-two" role="listitem">
                  <span className="vera-demo-index">02</span>
                  <strong>{t.coverDemoLink}</strong><small>{t.coverDemoLinkHint}</small>
                </div>
                <div className="vera-demo-check vera-demo-check-three" role="listitem">
                  <span className="vera-demo-index">03</span>
                  <strong>{t.coverDemoPayment}</strong><small>{t.coverDemoPaymentHint}</small>
                </div>
              </div>
              <div className="vera-demo-outcome">
                <ShieldAlert aria-hidden="true" />
                <span><small>{t.coverDemoNextStep}</small><strong>{t.coverDemoOutcome}</strong><em>{t.coverDemoOutcomeHint}</em></span>
                <ArrowRight aria-hidden="true" className="vera-demo-outcome-arrow" />
              </div>
              <p className="vera-demo-disclaimer">{t.coverDemoDisclaimer}</p>
            </article>

            {/* Veronica AI Interactive Copilot Card on the Cover */}
            <div
              className="vera-veronica-cover-banner"
              onClick={() => handleOpenVeronica(locale === "hi" ? "डिजिटल अरेस्ट कॉल के बारे में बताएं" : "What is a digital arrest call?")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  handleOpenVeronica();
                }
              }}
            >
              <VeraLogo className="vera-veronica-banner-avatar" />
              <div className="vera-veronica-banner-text">
                <span className="vera-veronica-banner-badge">{locale === "hi" ? "वेरोनिका त्वरित सहायता" : "VERONICA INSTANT COPILOT"}</span>
                <p>“{locale === "hi" ? "क्या पुलिस या सीबीआई स्काइप पर डिजिटल अरेस्ट कर सकती है?" : "Can police or CBI arrest someone on a Skype video call?"}”</p>
              </div>
              <span className="vera-veronica-banner-action">
                {locale === "hi" ? "वेरोनिका से पूछें →" : "Ask Veronica →"}
              </span>
            </div>
          </div>
        </div>

        <div className="vera-cover-feature-grid">
          {features.map((feature) => (
            <article
              className={`vera-cover-feature ${feature.isVeronica ? "vera-cover-feature-veronica" : ""}`}
              key={feature.number}
              onClick={feature.isVeronica ? () => handleOpenVeronica() : undefined}
              role={feature.isVeronica ? "button" : undefined}
              tabIndex={feature.isVeronica ? 0 : undefined}
              onKeyDown={(e) => {
                if (feature.isVeronica && (e.key === "Enter" || e.key === " ")) {
                  handleOpenVeronica();
                }
              }}
            >
              <div className="flex items-center justify-between">
                <span className="vera-cover-feature-number">{feature.number}</span>
                {feature.isVeronica && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider bg-amber-500/15 text-amber-600 dark:text-amber-300 border border-amber-500/30">
                    AI Assistant
                  </span>
                )}
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
              {feature.isVeronica && (
                <span className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-amber-700 dark:text-amber-300">
                  {locale === "hi" ? "बातचीत शुरू करें →" : "Start conversation →"}
                </span>
              )}
              <span className="vera-cover-feature-rule" aria-hidden="true" />
            </article>
          ))}
        </div>
      </section>

      <section className="vera-cover-limits" aria-labelledby="cover-limits-title">
        <div className="vera-cover-limits-copy">
          <p className="vera-cover-eyebrow"><span className="vera-cover-eyebrow-mark" aria-hidden="true" />{t.coverLimitsEyebrow}</p>
          <h2 id="cover-limits-title">{t.coverLimitsTitle}</h2>
          <p>{t.coverLimitsBody}</p>
        </div>
        <ul className="vera-cover-limit-list">
          {limits.map((limit) => <li key={limit}><span><Check aria-hidden="true" /></span>{limit}</li>)}
        </ul>
      </section>

      <footer className="vera-cover-footer">
        <div><h2>{t.coverClosingTitle}</h2><p>{t.coverClosingBody}</p></div>
        <button className="vera-cover-cta vera-cover-enter-cta" onClick={onEnter}>
          <span>{t.coverEnter}</span>
          <ArrowRight aria-hidden="true" />
        </button>
      </footer>
    </div>
  );
}
