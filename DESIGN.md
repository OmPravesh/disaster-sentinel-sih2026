---
name: Disaster Sentinel
description: Uttarakhand Multi-Hazard Autonomous Surveillance Network & Predictive Telemetry Command System
colors:
  primary: "#1340B4"
  primary-action: "#155DFC"
  primary-command: "#6425FE"
  neutral-bg: "#F9FAFB"
  neutral-surface: "#FFFFFF"
  neutral-dark-bg: "#0B0F19"
  neutral-dark-surface: "#131B2E"
  hazard-critical: "#FB2C36"
  hazard-warning: "#FF6900"
  hazard-safe: "#16A34A"
  hazard-info: "#0284C7"
typography:
  display:
    fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  title:
    fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0em"
  body:
    fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0em"
  label:
    fontFamily: "'JetBrains Mono', monospace"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.04em"
rounded:
  sm: "6px"
  md: "10px"
  lg: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary-action}"
    textColor: "{colors.neutral-surface}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.primary}"
  card-telemetry:
    backgroundColor: "{colors.neutral-surface}"
    textColor: "{colors.neutral-dark-bg}"
    rounded: "{rounded.lg}"
    padding: "20px"
---

# Design System: Disaster Sentinel

## Overview

**Creative North Star: "The Alpine Sentinel"**

Disaster Sentinel operates in high-stakes emergency environments across Uttarakhand's river basins, unstable slope terrains, and pine perimeter forests. The visual system balances the rapid scanability of a mission-critical command console with the restraint, clarity, and ergonomic comfort required for long monitoring shifts. Every element communicates status, urgency, and confidence without overwhelming the operator.

The surface mode is **Operate**. Scanability, contrast, and cognitive calm outrank decorative expression. Information density is calibrated so telemetry from distributed edge nodes (LoRa SX1278 stations running on ESP32/Jetson) can be verified in a single visual sweep. Ambient states are quiet and grounded; breach states are vivid, unambiguous, and directional.

**Key Characteristics:**
- High-clarity typography featuring IBM Plex Sans for structured interfaces and JetBrains Mono for telemetry streams and sensor readings.
- High-contrast hazard semantics strictly reserved for life safety (Ruby Critical `#FB2C36`, Amber Warning `#FF6900`, Emerald Safe `#16A34A`, Cobalt Info `#0284C7`).
- Deep slate and midnight naval surfaces (`#0B0F19` and `#131B2E`) in dark mode with refined micro-borders (`slate-800`) to eliminate eye fatigue.
- Tabular numeric rhythm (`font-variant-numeric: tabular-nums`) preventing layout jitter during high-frequency LoRa packet arrivals.
- Soft elevation with calibrated offsets and diffuse blurs rather than harsh decorative drop shadows.

## Colors

The palette organizes into focused operational roles: primary navigation and command accents, a crisp high-legibility neutral scale, and life-critical hazard thresholds.

### Primary
- **Command Blue** (`#1340B4`): Grounded executive brand tone used for headers, primary controls, and active navigational anchor states.
- **Action Cobalt** (`#155DFC`): High-contrast interactive focal points, primary buttons, and link hovers.
- **Sentinel Violet** (`#6425FE`): AI inference and predictive trajectory horizon highlights (PyTorch GRU models on Jetson Orin Nano).

### Neutral
- **Page Canvas Light** (`#F9FAFB`): Cool, low-glare daytime background.
- **Card Panel Light** (`#FFFFFF`): Elevated white card surfaces with crisp `1px` subtle slate borders (`#E5E7EB`).
- **Page Canvas Dark** (`#0B0F19`): Deep alpine night canvas minimizing luminance in dark command rooms.
- **Card Panel Dark** (`#131B2E`): Slate-navy containment surface providing solid contrast for colored telemetry traces.
- **Muted Slate** (`#64748B` / `#94A3B8`): Contextual labels, units of measure, and axis markings meeting WCAG 2.1 AA 4.5:1 standards.

### Hazard Semantics
- **Ruby Critical** (`#FB2C36`): Immediate hazard breach, evacuation trigger, or hardware failure.
- **Amber Warning** (`#FF6900`): Threshold approach or rapid delta warning.
- **Emerald Safe** (`#16A34A`): Verified nominal readings and confirmed LoRa packet reception.
- **Cobalt Info** (`#0284C7`): Environmental context, particulate matter indicators, and baseline metrics.

### Named Rules
**The Hazard Exclusivity Rule.** Bright red and crimson are strictly forbidden as general decorative colors. Ruby is reserved exclusively for unacknowledged active alarms, threshold breaches, and emergency stop actions.

**The Tinted Neutral Rule.** On colored or dark backgrounds, secondary text is never pure neutral gray; it is tinted with a hint of slate or the card's native accent to maintain optical harmony.

## Typography

**Display Font:** IBM Plex Sans (with `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`)
**Body Font:** IBM Plex Sans
**Telemetry/Mono Font:** JetBrains Mono (with `"SF Mono", Consolas, monospace`)

**Character:** Technical, dependable, and legible down to 10px. The pairing balances the human authority of IBM Plex Sans with the precision of JetBrains Mono for sensor readings, coordinates, and packet metrics.

### Hierarchy
- **Display** (Bold 700, 2rem / 32px, line-height 1.2, tracking -0.02em): Top command greeting and executive summaries.
- **Headline** (SemiBold 600, 1.25rem / 20px, line-height 1.3): Major telemetry card titles and graph headers.
- **Title** (SemiBold 600, 0.875rem / 14px, line-height 1.4): Sector names, sub-panel headings, and station identities.
- **Body** (Regular 400, 0.875rem / 14px, line-height 1.5, max 70ch): Incident descriptions, AI forecast summaries, and status logs.
- **Label / Telemetry** (Mono SemiBold 600, 0.75rem / 12px, tabular-nums): Sensor values, threshold needle readouts, LoRa RSSI, and timestamps.

### Named Rules
**The Tabular Telemetry Rule.** All live numerical readouts (depth, tilt angle, TVOC ppb, PM2.5, RSSI) must declare `font-variant-numeric: tabular-nums` and monospace styling to prevent layout shifts as values fluctuate.

**The No-Eyebrow Rule.** Section headings carry their own hierarchy; redundant uppercase kicker tags stacked immediately above an existing heading are eliminated in favor of direct, self-explanatory headings.

## Layout

- **Grid Strategy:** Responsive 12-column CSS grid. Top sector metrics span 4 equal columns (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`). The middle operational deck uses a 3-5-4 column distribution (Hero Posture, Center Trajectory Forecaster, Real-time Snapshot Gauges). The bottom analytical deck uses an 8-4 split (Long-Horizon Horizon Forecast, Stations Watchlist).
- **Rhythm & Density:** Standard `16px` to `24px` gap spacing. Spacing above containers is always greater than internal child padding.
- **Breakpoints:** Mobile (<640px) stacks vertically; Tablet (640px–1024px) reveals 2-column sector cards; Desktop (≥1024px) establishes the full tripartite mission deck.

## Elevation & Depth

Surfaces rely on tonal layering and subtle ambient shadows rather than stark decorative drop shadows.

### Shadow Vocabulary
- **Subtle Surface** (`box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)`): Rest state for telemetry cards and data panels.
- **Lifted Interactive** (`box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.08), 0 2px 6px -2px rgba(0, 0, 0, 0.04)`): Hover state for interactive sector cards and action links.
- **Hazard Beacon Halo** (`box-shadow: 0 0 16px -2px rgba(251, 44, 54, 0.35)`): Ambient pulse around breached station indicators.

### Named Rules
**The Calm Surface Rule.** In nominal operating conditions, telemetry cards are quiet and flat at rest. Lift and glow appear only in response to operator hover or urgent sensor anomalies.

## Shapes

- **Radius Scale:** Base inputs and micro-badges use `6px` (`rounded-md`); navigation links and buttons use `10px` (`rounded-xl`); primary telemetry and chart panels use `16px` (`rounded-2xl`).
- **Pills:** Status badges and filter toggles use full pill geometry (`rounded-full`, `9999px`).
- **Borders:** Consistent `1px` subtle perimeter strokes (`border-slate-200/80` in light mode, `border-slate-800` in dark mode) provide clean container definition across all displays.

## Components

### Telemetry Cards
- **Shape:** Rounded 16px (`rounded-2xl`).
- **Background:** High-contrast clean white (`#FFFFFF`) in light mode; Slate-navy (`#131B2E`) in dark mode with a top accent indicator.
- **Hover:** Gentle `-1px` transform with soft ambient shadow lift.
- **Metrics:** Primary reading rendered in bold tabular mono (24px), unit rendered alongside in muted mono.

### Threshold Needle Gauges
- **Shape:** Full-radius track (`6px` height, `#E2E8F0` light / `#334155` dark).
- **Needle:** 3px rounded vertical pointer with smooth `0.4s cubic-bezier(0.4, 0, 0.2, 1)` transition for real-time tracking.
- **Limits:** Min/max labels with threshold breach points highlighted in semantic warning or critical tones.

### Status Badges & Pills
- **Style:** Compact pill (`rounded-full`), `font-mono`, `text-[10px]`, `font-bold`, uppercase.
- **Variants:**
  - *Safe:* Emerald tint (`bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300`).
  - *Warning:* Amber tint (`bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300`).
  - *Critical:* Rose/Ruby tint with soft pulse (`bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300`).

### Interactive Horizon Buttons
- **Style:** Segmented control pill (`bg-slate-100 dark:bg-slate-800`), containing active button with soft background lift and bold accent typography.

## Do's and Don'ts

### Do:
- **Do** format all sensor readings and numerical coordinates with `font-variant-numeric: tabular-nums` to eliminate jitter.
- **Do** test both light mode and dark mode for WCAG 2.1 AA text contrast (minimum 4.5:1 for body and labels).
- **Do** reserve crimson and ruby accents exclusively for real-time hazard breaches and critical hardware anomalies.
- **Do** provide clear units of measurement (meters, degrees, ppb, µg/m³) next to all live values.
- **Do** use smooth, gentle ease-out transitions (`cubic-bezier(0.4, 0, 0.2, 1)`) for charts, needles, and sidebar toggles.

### Don't:
- **Don't** use decorative gradient text or low-contrast pastel backgrounds that compromise rapid legibility.
- **Don't** use colored left borders or heavy 4px card borders.
- **Don't** use emoji or unstyled characters as telemetry icons; use unified FontAwesome or SVG vectors.
- **Don't** trigger disruptive full-screen modal takeovers for nominal background events; use the contextual simulation drawer and header notification pills.
