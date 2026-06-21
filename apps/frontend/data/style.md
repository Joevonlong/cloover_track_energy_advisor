# Heimwende Frontend Style Guide

Design system for the Heimwende energy advisor UI. Source of truth for extending the app without drifting from the established look.

## Design Direction

Heimwende is a consumer-facing energy advisor, not a business dashboard. The interface is dark and cinematic: a live satellite globe behind the user's address, with a floating white intake card and dark HUD panels for the proposal/results phase.

The product has two visual modes:

- **Intake:** dark globe background, centered white card floating over it, minimal form to collect household details.
- **Dashboard / Proposal:** full-viewport dark shell (deep teal-black gradient), Mapbox or Three.js globe panel, floating dark HUD panels with results data.

The aesthetic: "precision instrument, not a brochure."

## Tech Stack

- **Vite + React 18 + TypeScript** — app shell.
- **Tailwind CSS v3** — utility classes. `tailwind.config.js` extends the CSS variables.
- **CSS variables** — all tokens live in `src/index.css` under `:root` and `@layer components`.
- **lucide-react** — icon set. Use stroke icons; avoid mixing with other icon libraries.
- **TanStack Query v5** — data fetching and server state.
- **React Hook Form + Zod** — all forms.
- **Three.js** — 3D globe on the intake screen (`GlobeBackground`, `GlobeScene`).
- **Mapbox GL** — satellite map on the dashboard.
- **No animation library** — transitions are plain CSS (`transition` property, `@keyframes`).

## Tokens

CSS variables defined in `src/index.css`:

```css
/* Light surface tokens — used inside the intake card */
--bg: #ffffff;
--surface: #f2f4f9;
--surface-2: #e8eaf2;
--border: #e4e7ec;
--border-strong: #d0d5dd;
--text-1: #111827;
--text-2: #4b5563;
--text-3: #9ca3af;

--accent: #2f6fed;
--accent-soft: #eef3fd;
--accent-border: #bfcffb;

--success: #059669;   --success-soft: #ecfdf5;
--warning: #d97706;   --warning-soft: #fffbeb;
--danger:  #dc2626;   --danger-soft:  #fef2f2;
--info:    #0284c7;

/* Shadow tokens */
--shadow-sm:     0 1px 2px rgba(0,0,0,.04), 0 2px 6px -1px rgba(0,0,0,.06);
--shadow-md:     0 4px 16px rgba(0,0,0,.08);
--shadow-tinted: 0 1px 2px rgba(0,0,0,.04), 0 4px 8px -2px rgba(0,0,0,.06);
--shadow-accent: 0 0 0 1px rgba(47,111,237,.12), 0 4px 12px -2px rgba(47,111,237,.15);

/* Easing */
--ease-out-strong:    cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out-strong: cubic-bezier(0.77, 0, 0.175, 1);
```

## Color Usage

### Dark shell (dashboard, globe)
- Page/shell background: `#071014` or the teal-black gradient in `.dashboard-shell`.
- HUD panels: `rgb(9 17 20 / 0.78)`, `backdrop-filter: blur(18px)`.
- Panel borders: `rgb(255 255 255 / 0.13)`.
- Body text: `#edf7f2`.
- Secondary text: `#b7c7c0`, `#91a39d`.
- Primary action button: `background: #d9f99d; color: #18200d` (lime-on-dark).
- Secondary action button: `rgb(255 255 255 / 0.08)` with white border at 13% opacity.
- Inputs: `rgb(255 255 255 / 0.08)` background, teal focus ring `rgb(125 211 199 / 0.82)`.
- Panel icon accent: teal (`#7dd3c7`, `rgb(20 184 166 / 0.13)` background).

### Light intake card
Use the CSS variable tokens above. The card is `bg-white` on the dark globe.
- Primary button: `bg-accent text-white`.
- Focus ring: `2px solid var(--accent)`.

Never use the dark HUD colors inside the light intake card, and vice versa.

## Typography

Font stack: `Inter, ui-sans-serif, system-ui, -apple-system, sans-serif` (loaded from system/CDN, no custom font loader).

Global settings (in `@layer base`):
```css
font-variant-numeric: tabular-nums;
-webkit-font-smoothing: antialiased;
```

Common scale:
- HUD panel title: `15px`, `font-weight: 700`.
- Section headings: `13px`, `font-weight: 700`, color `#f9fffc`.
- Control labels: `12px`, `font-weight: 700`, color `#b7c7c0`.
- Body / row text: `12px`–`13px`.
- Kicker / metadata labels: `11px`, uppercase, `letter-spacing: 0.08em`, `font-weight: 700`, color `#91a39d`.
- Summary metric values: `18px`, `font-weight: 800`, white.

Use tabular nums for all numeric output (`font-variant-numeric: tabular-nums` is global).

## Layout

### Intake screen (`.intake-screen`)
- Full viewport, `position: relative`, globe fills 100%.
- `.intake-scrim` — dark radial vignette over the globe, `z-index: 1`, pointer-events none.
- `.intake-overlay` — absolute, full viewport, `z-index: 2`, centers the card with flex, `pointer-events: none` so globe stays interactive. Children re-enable with `pointer-events: auto`.
- Card max-width: `max-w-md` (~448px).

### Dashboard shell (`.dashboard-shell`)
- Full viewport, deep teal-black gradient background, no page scroll intended.
- `.background-grid` — subtle dot/line grid overlay, `z-index: 1`, fades out with mask.
- `.globe-panel` — absolute, fills viewport, `z-index: 0`.
- HUD panels float over the globe with `position: absolute`, `z-index: 5`.

### HUD panel variants
- **Bottom bar** (`.hud-panel-start`): centered bottom, `max-width: min(880px, calc(100vw - 32px))`, `bottom: 28px`.
- **Compact rail** (`.hud-panel-compact`): top-left, `width: min(392px, calc(100vw - 40px))`.
- **Expanded sheet** (`.hud-panel-expanded`): top-right, fixed width `min(470px, ...)`, full height with scroll.

## Spacing

- HUD panel padding: `padding: 12px` body, `padding: 16px` headers.
- Panel section padding: `padding: 12px`.
- Grid gap inside panels: `gap: 10px`–`gap: 12px`.
- Control label margin-bottom: `6px`.
- Input padding: `10px 11px`.
- Action button height: `min-height: 38px`, padding `0 13px`.

## Shape and Radius

- HUD panels and inputs: `border-radius: 7px`–`8px`.
- Panel icon squares: `border-radius: 7px`.
- Pill/chip: `border-radius: 999px`.
- Intake card: `rounded-2xl` (Tailwind).
- Intake form inputs: `rounded-lg`.

No large modal overlays or nested-card patterns — the globe is the canvas; panels float over it.

## Core Components

### `.hud-panel`
The base class for all floating panels:
```css
position: relative;
z-index: 5;
border: 1px solid rgb(255 255 255 / 0.13);
border-radius: 8px;
background: rgb(9 17 20 / 0.78);
color: #edf7f2;
box-shadow: 0 22px 90px rgb(0 0 0 / 0.36);
backdrop-filter: blur(18px);
```

### Buttons (dark context)
Primary (lime):
```css
background: #d9f99d;
color: #18200d;
border-radius: 7px;
font-size: 12px;
font-weight: 800;
min-height: 38px;
padding: 0 13px;
```

Secondary:
```css
border: 1px solid rgb(255 255 255 / 0.13);
background: rgb(255 255 255 / 0.08);
color: #edf7f2;
```

Hover for all: `transform: translateY(-1px); border-color: rgb(255 255 255 / 0.28)`.
Use `transition: transform 160ms ease, border-color 160ms ease, background-color 160ms ease`.

### Inputs (dark context — `.control-input`)
```css
border: 1px solid rgb(255 255 255 / 0.14);
border-radius: 7px;
background: rgb(255 255 255 / 0.08);
padding: 10px 11px;
color: #ffffff;
```
Focus: `border-color: rgb(125 211 199 / 0.82); box-shadow: 0 0 0 3px rgb(125 211 199 / 0.16)`.

### Status chip (`.status-chip`)
```css
border: 1px solid rgb(255 255 255 / 0.12);
border-radius: 7px;
background: rgb(255 255 255 / 0.06);
padding: 9px 10px;
font-size: 12px;
color: #bacbc4;
```
Error state: `border-color: rgb(248 113 113 / 0.38); background: rgb(127 29 29 / 0.22); color: #fecaca`.

### Metric cards (`.summary-metric-card`)
```css
border: 1px solid rgb(255 255 255 / 0.1);
border-radius: 8px;
background: rgb(255 255 255 / 0.045);
padding: 10px;
```
Label: `11px`, color `#93a49f`. Value: `18px`, `font-weight: 800`, white.

### Kicker labels (`.panel-kicker`)
```css
color: #91a39d;
font-size: 11px;
font-weight: 700;
letter-spacing: 0.08em;
text-transform: uppercase;
margin: 0;
```

### Panel icon square (`.panel-section-icon`)
```css
display: inline-grid;
width: 30px; height: 30px;
place-items: center;
border: 1px solid rgb(167 243 208 / 0.18);
border-radius: 7px;
background: rgb(20 184 166 / 0.13);
color: #7dd3c7;
```

## Transitions

No animation library. Use CSS only.

- Button hover lift: `transform: translateY(-1px)`, `160ms ease`.
- Input focus ring: `border-color 150ms ease, box-shadow 150ms ease`.
- Address suggestion dropdown: `@keyframes address-suggest-in` (opacity 0→1, `scale(0.98) translateY(-4px)` → none), `150ms var(--ease-out-strong)`. Class `.address-suggest`.
- State change text / chips: `150ms`–`200ms ease`.

Never animate `width`, `height`, or other layout-heavy properties.

Respect `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }
}
```

## Mapbox

Popup styling is overridden in `index.css`:
- `.mapboxgl-popup-content`: dark `rgb(10 18 22 / 0.94)`, `border-radius: 8px`, white-alpha border.
- `.mapboxgl-popup-tip`: match background color.

Always provide a fallback (`.globe-stage-fallback` / `.mapbox-message`) when the Mapbox token is absent.

## Accessibility

Focus visible:
```css
:where(button, a, input, select):focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

- Use semantic elements (`button`, `input`, `select`).
- Never go below `11px` text in interactive or reading contexts.
- `.sr-only` is defined globally — use it for icon-only buttons.
- Keep disabled states visually muted with `cursor-not-allowed`.

## Responsive

Breakpoint: `max-width: 760px`.
- `.hud-panel-start` collapses to `calc(100vw - 24px)`, stacks to 2-column grid.
- `.hud-panel-compact` narrows to `calc(100vw - 24px)`, capped at `46vh`.
- `.hud-panel-expanded` goes full-bleed inset `12px` on mobile.
- Summary metric grid and plot grid collapse to single column.

## Do and Do Not

Do:
- Use dark HUD tokens in dark contexts and light card tokens in the intake card — never mix them.
- Use `lucide-react` for all icons.
- Use tabular-nums for all numbers.
- Use the `.hud-panel` base class for any new floating panel.
- Use `transition: transform 160ms ease, ...` for hover/press feedback.
- Use `border-radius: 7px`–`8px` for panels and inputs; `999px` for pills.

Do not:
- Add GSAP, Framer Motion, or any animation library — CSS transitions only.
- Use Phosphor icons or any icon set other than lucide-react.
- Add Tailwind v4 syntax (`@import "tailwindcss"`, `@theme`) — this project is Tailwind v3.
- Use Next.js patterns (app router, server components) — this is a Vite SPA.
- Put a light background or marketing copy inside the dark dashboard shell.
- Animate from `scale(0)` — start from `scale(0.98)` at minimum.
- Use `overflow: hidden` on the globe container (breaks Three.js/Mapbox rendering).
