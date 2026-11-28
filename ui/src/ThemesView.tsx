import { useRef, useState } from "react";

import { fetchThemeSheets, fetchThemes, useLoad } from "./api";
import { Empty, Loading } from "./components";
import { SEASONS, isSeasonId } from "./season";
import { writeHidden } from "./useSeason";
import {
  type Choice,
  type ThemeInfo,
  type ThemeStatus,
  COOKIES_AT_LOAD,
  applyTheme,
  choiceCookies,
  comingSoon,
  dateRange,
  pickTheme,
  readChoice,
  removeTheme,
  setAuto,
  themeStatus,
} from "./themes";

const STATUS: Record<ThemeStatus, { label: string; tone: string }> = {
  applied: { label: "Applied", tone: "on" },
  showing: { label: "Showing now", tone: "on" },
  removed: { label: "Removed", tone: "off" },
  waiting: { label: "Not in season", tone: "idle" },
  soon: { label: "Coming soon", tone: "idle" },
};

const LIVE_ID = "dagwick-live-theme";

/**
 * Airflow draws the theme it was given when the page loaded. To change it without a
 * reload, Dagwick adds a stylesheet: the new theme, or one that hides the loaded theme.
 */
function setLiveCss(css: string) {
  let el = document.getElementById(LIVE_ID);
  if (!el) {
    el = document.createElement("style");
    el.id = LIVE_ID;
    document.head.appendChild(el);
  }
  el.textContent = css;
}

export function ThemesView() {
  const { data, error, reload } = useLoad((s) => fetchThemes(s), []);
  if (error)
    return (
      <Empty
        title="Couldn't load the themes"
        body={error}
        action={
          <button className="dagwick-btn" onClick={reload}>
            Try again
          </button>
        }
      />
    );
  if (!data) return <Loading label="Loading themes…" />;
  return <Themes themes={data} />;
}

function Themes({ themes }: { themes: ThemeInfo[] }) {
  const [choice, setChoice] = useState<Choice>(() => readChoice(document.cookie));
  // What Airflow drew when this page loaded; every change is applied on top of that.
  const loaded = useRef(pickTheme(themes, readChoice(COOKIES_AT_LOAD)));
  const [busy, setBusy] = useState<string>();
  const [problem, setProblem] = useState<string>();
  const [notice, setNotice] = useState<string>();

  const change = async (next: Choice, label: string) => {
    setBusy(label);
    setProblem(undefined);
    setNotice(undefined);
    try {
      const want = pickTheme(themes, next);
      const from = loaded.current;
      let css = "";
      if (want && want !== from) {
        const [drawn, old] = await Promise.all([fetchThemeSheets(want), from ? fetchThemeSheets(from) : undefined]);
        css = (old?.reset ?? "") + drawn.css;
      } else if (!want && from) css = (await fetchThemeSheets(from)).hide;
      for (const c of choiceCookies(next)) document.cookie = c;
      setLiveCss(css);
      setChoice(next);
      // A theme shows everywhere at once: Airflow and Dagwick's banner (even if the
      // viewer once hid the banner's seasonal look).
      const shown = themes.find((t) => t.id === want);
      if (shown) writeHidden(false);
      setNotice(shown ? `${shown.name} is on, across Airflow and on Dagwick's banner.` : "No theme is showing now.");
    } catch (e) {
      setProblem(e instanceof Error ? e.message : "Couldn't change the theme");
    } finally {
      setBusy(undefined);
    }
  };

  return (
    <section className="dagwick-themes">
      <header className="dagwick-themes-head">
        <h2>Seasonal themes</h2>
        <p className="dagwick-muted">
          Themes decorate all of Airflow, not only Dagwick. Your choices are saved in this browser and only change what
          you see.
        </p>
      </header>

      <div className="dagwick-theme-settings">
        <label className="dagwick-switch">
          <input
            type="checkbox"
            role="switch"
            checked={choice.auto}
            disabled={!!busy}
            onChange={(e) => change(setAuto(choice, e.target.checked), "auto")}
          />
          <span className="dagwick-switch-track" aria-hidden="true" />
          <span className="dagwick-switch-text">
            <strong>Show themes on their dates</strong>
            <small className="dagwick-muted">
              {choice.auto
                ? "Each theme appears by itself on its dates and goes away afterwards."
                : "Nothing appears by itself, Dagwick's banner included. Apply a theme below whenever you like."}
            </small>
          </span>
        </label>
      </div>

      <p className="dagwick-theme-notice" role="status" aria-live="polite">
        {notice}
      </p>

      {problem && (
        <p className="dagwick-theme-problem" role="alert">
          {problem}
        </p>
      )}

      <div className="dagwick-theme-list">
        {/* Only themes that can be applied; one coming soon shows up once it's decorated. */}
        {themes
          .filter((t) => !comingSoon(t))
          .map((t) => {
            const status = themeStatus(t, themes, choice);
            const on = status === "applied" || status === "showing";
            const s = STATUS[status];
            return (
              <article key={t.id} className={`dagwick-theme${on ? " is-on" : ""}`}>
                <Scene id={t.id} />
                <div className="dagwick-theme-body">
                  <div className="dagwick-theme-title">
                    <h3>{t.name}</h3>
                    <span className={`dagwick-theme-status is-${s.tone}`}>{s.label}</span>
                  </div>
                  <p className="dagwick-theme-dates">{t.when ?? `${dateRange(t.start, t.end)} · every year`}</p>
                  <p className="dagwick-muted">{t.description}</p>
                  <div className="dagwick-theme-actions">
                    {status === "soon" ? (
                      <button className="dagwick-btn" disabled>
                        Coming soon
                      </button>
                    ) : on ? (
                      <button
                        className="dagwick-btn"
                        disabled={!!busy}
                        onClick={() => change(removeTheme(themes, choice, t.id), t.id)}
                      >
                        {busy === t.id ? "Removing…" : "Remove theme"}
                      </button>
                    ) : (
                      <button
                        className="dagwick-btn dagwick-btn-primary"
                        disabled={!!busy}
                        onClick={() => change(applyTheme(choice, t.id), t.id)}
                      >
                        {busy === t.id ? "Applying…" : "Apply theme"}
                      </button>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
      </div>
    </section>
  );
}

/** A small still picture of a theme, for its card. */
function Scene({ id }: { id: string }) {
  if (id === "halloween") return <HalloweenScene />;
  if (id === "christmas") return <SnowScene />;
  if (id === "newroz") return <NewrozScene />;
  if (id === "lunar-new-year") return <LanternScene />;
  return <BannerScene id={id} />;
}

/** Colours for the themes that so far only change the banner. */
const BANNER_SCENES: Record<string, [string, string]> = {
  newroz: ["#14532d", "#b91c1c"],
  eid: ["#3b2a07", "#a16207"],
  ramadan: ["#0b2a3a", "#134e4a"],
  "new-year": ["#1e1b4b", "#3730a3"],
  "language-day": ["#422006", "#b45309"],
  birthday: ["#500724", "#be185d"],
  diwali: ["#431407", "#c2410c"],
  "carsema-sor": ["#14532d", "#dc2626"],
};

/** A simple picture for a banner-only theme: its colours and its sign. */
function BannerScene({ id }: { id: string }) {
  const [from, to] = BANNER_SCENES[id] ?? ["#1f2937", "#374151"];
  const season = isSeasonId(id) ? SEASONS[id] : undefined;
  return (
    <svg className="dagwick-theme-scene" viewBox="0 0 220 110" role="img" aria-label={season?.name ?? id}>
      <defs>
        <linearGradient id={`dagwick-bs-${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={from} />
          <stop offset="1" stopColor={to} />
        </linearGradient>
      </defs>
      <rect width="220" height="110" fill={`url(#dagwick-bs-${id})`} />
      <text x="110" y="70" textAnchor="middle" fontSize="44">
        {season?.icon ?? "✨"}
      </text>
    </svg>
  );
}

function HalloweenScene() {
  const bats: [number, number, number, number][] = [
    [70, 26, 0.55, -10],
    [128, 18, 0.4, 8],
    [176, 40, 0.7, -4],
    [40, 52, 0.35, 12],
  ];
  const embers: [number, number, number][] = [
    [30, 88, 1.6],
    [96, 70, 1.2],
    [150, 84, 1.8],
    [196, 64, 1.1],
    [118, 94, 1.3],
  ];
  return (
    <svg className="dagwick-theme-scene" viewBox="0 0 220 110" role="img" aria-label="Bats over a foggy night">
      <defs>
        <radialGradient id="dagwick-hw-moon">
          <stop offset="0" stopColor="#fde68a" />
          <stop offset="1" stopColor="#f59e0b" />
        </radialGradient>
        <radialGradient id="dagwick-hw-ember">
          <stop offset="0" stopColor="#fff3c4" />
          <stop offset=".4" stopColor="#fb923c" />
          <stop offset="1" stopColor="#f97316" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="220" height="110" fill="#1d1430" />
      <circle cx="176" cy="30" r="26" fill="#f59e0b" opacity=".12" />
      <circle cx="176" cy="30" r="15" fill="url(#dagwick-hw-moon)" />
      {bats.map(([x, y, s, r], i) => (
        <path
          key={i}
          transform={`translate(${x} ${y}) rotate(${r}) scale(${s})`}
          fill="#0d0714"
          d="M0 -2 C2 -6 6 -6 8 -3 C10 -6 14 -7 18 -4 C15 -3 14 0 15 3 C12 1 9 2 8 4 C6 2 3 2 0 5 C-3 2 -6 2 -8 4 C-9 2 -12 1 -15 3 C-14 0 -15 -3 -18 -4 C-14 -7 -10 -6 -8 -3 C-6 -6 -2 -6 0 -2Z"
        />
      ))}
      {embers.map(([x, y, r], i) => (
        <circle key={i} cx={x} cy={y} r={r * 2.4} fill="url(#dagwick-hw-ember)" />
      ))}
      <ellipse cx="60" cy="104" rx="90" ry="14" fill="#7c3aed" opacity=".35" />
      <ellipse cx="170" cy="106" rx="80" ry="12" fill="#4c1d95" opacity=".45" />
    </svg>
  );
}

/** Newroz: the Kurdish sun over mountains with bonfires on their peaks. */
function NewrozScene() {
  const rays = Array.from({ length: 21 }, (_, i) => {
    const a = (2 * Math.PI * i) / 21 - Math.PI / 2;
    const h = Math.PI / 42;
    const p = (r: number, b: number) => `${(182 + r * Math.cos(b)).toFixed(1)} ${(30 + r * Math.sin(b)).toFixed(1)}`;
    return `M${p(10, a - h)} L${p(19, a)} L${p(10, a + h)}Z`;
  }).join(" ");
  const fires: [number, number][] = [
    [66, 66],
    [150, 72],
  ];
  return (
    <svg
      className="dagwick-theme-scene"
      viewBox="0 0 220 110"
      role="img"
      aria-label="The Kurdish sun over mountains with bonfires and torches"
    >
      <defs>
        <linearGradient id="dagwick-nz-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0f1f2a" />
          <stop offset="1" stopColor="#3a2a1c" />
        </linearGradient>
        <radialGradient id="dagwick-nz-glow">
          <stop offset="0" stopColor="#fb923c" stopOpacity=".6" />
          <stop offset="1" stopColor="#fb923c" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="220" height="110" fill="url(#dagwick-nz-sky)" />
      {[118, 140, 162].map((a) => {
        const r = (d: number) => (a + d) * (Math.PI / 180);
        const p = (d: number) => `${182 + 170 * Math.cos(r(d))} ${30 + 170 * Math.sin(r(d))}`;
        return <path key={a} d={`M182 30 L${p(-3)} L${p(3)}Z`} fill="#fde68a" opacity=".07" />;
      })}
      <circle cx="182" cy="30" r="24" fill="#fde68a" opacity=".12" />
      <path d={rays} fill="#fbbf24" />
      <circle cx="182" cy="30" r="8" fill="#fbbf24" />
      <g fill="none" strokeWidth="1.2" strokeLinecap="round">
        <path d="M0 70 C24 60 40 52 64 56 S104 72 128 60 S176 44 220 58" stroke="#a7d3c2" opacity=".35" />
        <path d="M0 84 C20 76 40 70 66 66 S112 80 150 72 S200 82 220 78" stroke="#a7d3c2" opacity=".55" />
        <path d="M0 98 C30 92 50 86 80 90 S140 100 170 94 S210 92 220 96" stroke="#fbbf24" opacity=".6" />
      </g>
      {[
        [18, 92, "n"],
        [28, 96, "t"],
        [200, 94, "n"],
      ].map(([x, y, kind]) => (
        <g key={x} transform={`translate(${x} ${y})`}>
          <path d={`M0 0 V${110 - Number(y)}`} stroke="#4d7c4f" strokeWidth="1.2" />
          {kind === "t" ? (
            <path d="M-3 -1 C-4 -6 -2 -8 0 -9 C2 -8 4 -6 3 -1 C2 1 -2 1 -3 -1Z" fill="#dc2626" />
          ) : (
            <>
              <circle r="3.4" fill="#fffdf5" />
              <circle r="1.4" fill="#f59e0b" />
            </>
          )}
        </g>
      ))}
      {fires.map(([x, y]) => (
        <g key={x} transform={`translate(${x} ${y})`}>
          <circle cy="-6" r="16" fill="url(#dagwick-nz-glow)" />
          <path d="M0 0 C-5 -3 -3 -9 0 -15 C3 -9 5 -3 0 0Z" fill="#f97316" />
          <path d="M0 0 C-3 -2 -2 -6 0 -10 C2 -6 3 -2 0 0Z" fill="#facc15" />
        </g>
      ))}
      {[
        [80, 40],
        [140, 48],
        [60, 30],
        [120, 56],
      ].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="1.2" fill="#fdba74" opacity=".8" />
      ))}
      {[
        [112, 79],
        [120, 78],
        [128, 76.5],
        [136, 75],
        [143, 73.6],
      ].map(([x, y]) => (
        <g key={x}>
          <circle cx={x} cy={y} r="2.4" fill="#fb923c" opacity=".35" />
          <circle cx={x} cy={y} r=".7" fill="#ffe3a3" />
        </g>
      ))}
    </svg>
  );
}

/** Lunar New Year: red lanterns on a string, the full moon and rising sky lanterns. */
function LanternScene() {
  const hanging: [number, number, number][] = [
    [30, 22, 1],
    [72, 34, 0.85],
    [112, 26, 1.05],
    [152, 36, 0.9],
  ];
  const sky: [number, number, number][] = [
    [40, 92, 1],
    [96, 76, 0.75],
    [150, 96, 0.9],
    [196, 70, 0.6],
  ];
  const stars: [number, number][] = [
    [18, 40],
    [58, 58],
    [92, 44],
    [140, 60],
    [168, 50],
    [206, 56],
    [120, 16],
  ];
  const plum: [number, number, string][] = [
    [14, 92, "#f48fb1"],
    [22, 84, "#fbd3df"],
    [30, 80, "#e0457b"],
    [40, 77, "#f48fb1"],
    [12, 82, "#fbd3df"],
  ];
  return (
    <svg
      className="dagwick-theme-scene"
      viewBox="0 0 220 110"
      role="img"
      aria-label="Red lanterns, sky lanterns and a shooting star under a full moon, with plum blossom"
    >
      <defs>
        <linearGradient id="dagwick-lf-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#141a33" />
          <stop offset="1" stopColor="#3a1a1f" />
        </linearGradient>
        <radialGradient id="dagwick-lf-red" cx=".45" cy=".45" r=".65">
          <stop offset="0" stopColor="#ffd59a" />
          <stop offset=".35" stopColor="#f8613a" />
          <stop offset=".8" stopColor="#d61f1f" />
          <stop offset="1" stopColor="#7f1414" />
        </radialGradient>
        <radialGradient id="dagwick-lf-halo">
          <stop offset="0" stopColor="#ffb46b" stopOpacity=".55" />
          <stop offset="1" stopColor="#ff8a3d" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="220" height="110" fill="url(#dagwick-lf-sky)" />
      <circle cx="186" cy="28" r="22" fill="#ffe7a8" opacity=".12" />
      <circle cx="186" cy="28" r="12" fill="#f8e3a8" />
      {stars.map(([x, y]) => (
        <circle key={`${x}-${y}`} cx={x} cy={y} r=".7" fill="#fff6dc" opacity=".6" />
      ))}
      <defs>
        <linearGradient id="dagwick-lf-tail" x1="1" y1="0" x2="0" y2="0">
          <stop offset="0" stopColor="#fffbe8" />
          <stop offset="1" stopColor="#ffd76a" stopOpacity="0" />
        </linearGradient>
      </defs>
      <g transform="translate(150 46) rotate(24)">
        <rect x="-34" y="-.6" width="34" height="1.2" rx=".6" fill="url(#dagwick-lf-tail)" />
        <circle r="3" fill="#fffbe8" opacity=".25" />
        <circle r="1" fill="#fffbe8" />
      </g>
      <path d="M0 8 Q55 26 110 8 T220 8" fill="none" stroke="#5b4630" strokeWidth=".8" />
      {sky.map(([x, y, s]) => (
        <g key={x} transform={`translate(${x} ${y}) scale(${s})`}>
          <circle r="11" fill="url(#dagwick-lf-halo)" />
          <path d="M-4 -6 Q0 -8 4 -6 L3 4 Q0 5 -3 4Z" fill="#ffc25c" />
          <ellipse cy="4" rx="3" ry=".8" fill="#fff8dc" />
        </g>
      ))}
      {hanging.map(([x, drop, s]) => (
        <g key={x} transform={`translate(${x} ${8 + Math.sin((x / 220) * Math.PI * 2) * 4}) scale(${s})`}>
          <path d={`M0 0 V${drop - 10}`} stroke="#5b4630" strokeWidth=".6" />
          <g transform={`translate(0 ${drop - 10})`}>
            <circle cy="9" r="14" fill="url(#dagwick-lf-halo)" />
            <rect x="-3" y="0" width="6" height="2" rx=".6" fill="#e9b949" />
            <ellipse cy="9" rx="8" ry="7.2" fill="url(#dagwick-lf-red)" />
            <rect x="-3.4" y="15.6" width="6.8" height="2" rx=".6" fill="#e9b949" />
            <path d="M0 17.6 V24" stroke="#c81e1e" strokeWidth="1" />
          </g>
        </g>
      ))}
      <path
        d="M0 104 L10 94 L14 84 L24 80 L40 76 M14 84 L12 76"
        fill="none"
        stroke="#4a2e26"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {plum.map(([x, y, c]) => (
        <g key={`${x}-${y}`} transform={`translate(${x} ${y})`}>
          {[0, 72, 144, 216, 288].map((r) => (
            <circle key={r} cy="-1.9" r="2" fill={c} transform={`rotate(${r})`} />
          ))}
          <circle r=".9" fill="#b3123f" />
        </g>
      ))}
    </svg>
  );
}

/** The snow theme's picture. */
function SnowScene() {
  const flakes: [number, number, number][] = [
    [26, 22, 7],
    [70, 46, 5],
    [112, 18, 9],
    [150, 52, 6],
    [190, 26, 7],
    [48, 64, 4],
    [132, 74, 4],
  ];
  return (
    <svg className="dagwick-theme-scene" viewBox="0 0 220 110" role="img" aria-label="Snow falling over Airflow">
      <rect width="220" height="110" fill="#1b2433" />
      {flakes.map(([x, y, r], i) => (
        <g
          key={i}
          transform={`translate(${x} ${y}) rotate(${i * 13})`}
          stroke="#fff"
          strokeWidth={r / 6}
          strokeLinecap="round"
          fill="none"
          opacity={0.45 + (i % 3) * 0.15}
        >
          {[0, 60, 120, 180, 240, 300].map((a) => (
            <path
              key={a}
              transform={`rotate(${a})`}
              d={`M0 0 V${-r} M0 ${-r * 0.45} l${-r * 0.22} ${-r * 0.2} M0 ${-r * 0.45} l${r * 0.22} ${-r * 0.2}`}
            />
          ))}
        </g>
      ))}
      <path d="M0 96 C30 86 60 88 90 94 S150 102 180 92 S210 86 220 90 V110 H0Z" fill="#eef4fa" />
    </svg>
  );
}
