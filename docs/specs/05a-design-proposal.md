# Design Proposal: Meal Planner React + shadcn/ui

**Status:** ✅ Approved (2026-05-03)  
**Parent spec:** `05-react-shadcn-frontend.md`  
**Date:** 2026-05-04

---

## Design Direction

A minimal, restrained interface inspired by Linear and Vercel — clean typography, generous whitespace, and a muted color palette. The design should feel like a productivity tool that happens to be about food, not a typical loud food app.

---

## Colour Palette

### Accent Colour Options

| Option | Name | Hex | Rationale |
|--------|------|-----|-----------|
| **A (Recommended)** | Sage | `#7C9082` | A desaturated green-gray that feels organic and fresh without being "health app green." Subtle nod to ingredients/freshness while maintaining the restrained palette of Linear-style interfaces. |
| B | Terracotta Gold | `#C4956A` | A muted, earthy amber that evokes warmth and appetite without falling into red/orange territory. References clay cookware and natural ingredients. |
| C | Deep Aubergine | `#5E4B56` | A purple-brown hybrid that's unexpected in food apps. Echoes Linear's signature purple but warmed with brown undertones. Feels premium and editorial. |

**Recommendation:** Option A (Sage) — it balances the food context with the minimal aesthetic. The muted green suggests freshness without screaming "health food."

### Neutral Scale (Zinc)

Using Tailwind's Zinc palette for consistency with shadcn/ui defaults:

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `background` | `#FAFAFA` (zinc-50) | `#09090B` (zinc-950) | Page background |
| `foreground` | `#18181B` (zinc-900) | `#FAFAFA` (zinc-50) | Primary text |
| `card` | `#FFFFFF` | `#18181B` (zinc-900) | Card surfaces |
| `card-foreground` | `#18181B` (zinc-900) | `#FAFAFA` (zinc-50) | Card text |
| `muted` | `#F4F4F5` (zinc-100) | `#27272A` (zinc-800) | Subtle backgrounds |
| `muted-foreground` | `#71717A` (zinc-500) | `#A1A1AA` (zinc-400) | Secondary text |
| `border` | `#E4E4E7` (zinc-200) | `#27272A` (zinc-800) | Borders, dividers |
| `input` | `#E4E4E7` (zinc-200) | `#27272A` (zinc-800) | Input borders |

### Semantic Colours

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `primary` | `#7C9082` (Sage) | `#7C9082` | Primary actions, active states |
| `primary-foreground` | `#FFFFFF` | `#FFFFFF` | Text on primary |
| `secondary` | `#F4F4F5` | `#27272A` | Secondary buttons |
| `secondary-foreground` | `#18181B` | `#FAFAFA` | Text on secondary |
| `destructive` | `#DC2626` (red-600) | `#EF4444` (red-500) | Delete actions, errors |
| `destructive-foreground` | `#FFFFFF` | `#FFFFFF` | Text on destructive |
| `accent` | `#F4F4F5` | `#27272A` | Hover states |
| `accent-foreground` | `#18181B` | `#FAFAFA` | Text on accent |

### Additional Semantic

| Purpose | Light Mode | Dark Mode |
|---------|------------|-----------|
| Success | `#16A34A` (green-600) | `#22C55E` (green-500) |
| Warning | `#CA8A04` (yellow-600) | `#EAB308` (yellow-500) |
| Info | `#2563EB` (blue-600) | `#3B82F6` (blue-500) |

---

## Typography

### Font Family

**Geist Sans** — Vercel's typeface, designed for interfaces. Clean, modern, excellent readability at all sizes. Available via Fontsource or Vercel's CDN.

```css
--font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

Fallback to system fonts ensures fast initial render.

### Type Scale

| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `h1` | 36px (2.25rem) | 600 | 1.2 | Page titles |
| `h2` | 24px (1.5rem) | 600 | 1.3 | Section headers |
| `h3` | 20px (1.25rem) | 600 | 1.4 | Card titles, subsections |
| `h4` | 16px (1rem) | 600 | 1.4 | Small headers |
| `body` | 16px (1rem) | 400 | 1.5 | Default text |
| `body-sm` | 14px (0.875rem) | 400 | 1.5 | Secondary content |
| `small` | 12px (0.75rem) | 400 | 1.4 | Captions, labels |
| `muted` | 14px (0.875rem) | 400 | 1.5 | De-emphasized text (uses `muted-foreground` color) |

### Font Weights

Limited to three weights for consistency:
- **400 (Regular)** — Body text, descriptions
- **500 (Medium)** — Emphasis, labels
- **600 (Semibold)** — Headings, buttons

---

## Spacing & Layout

### Base Unit

**4px** — Tailwind's default spacing scale. All spacing derives from this.

### Spacing Scale (commonly used)

| Token | Value | Usage |
|-------|-------|-------|
| `1` | 4px | Tight gaps (icon-to-text) |
| `2` | 8px | Inline spacing |
| `3` | 12px | Small component padding |
| `4` | 16px | Standard padding |
| `6` | 24px | Section gaps |
| `8` | 32px | Large section gaps |
| `12` | 48px | Page section margins |
| `16` | 64px | Major layout breaks |

### Layout

| Property | Value |
|----------|-------|
| Content max-width | `1280px` (max-w-7xl) |
| Page padding (mobile) | `16px` (p-4) |
| Page padding (desktop) | `32px` (p-8) |
| Card gap (grid) | `24px` (gap-6) |
| Nav height | `64px` |

### Border Radius

Single `--radius` variable at `0.5rem` (8px), deriving the full scale:

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 4px | Small elements, badges |
| `radius-md` | 6px | Inputs, small buttons |
| `radius-lg` | 8px | Cards, modals |
| `radius-xl` | 12px | Large cards, hero sections |
| `radius-full` | 9999px | Avatars, pills |

---

## Component Personality

### Buttons

| Variant | Style |
|---------|-------|
| **Primary** | Sage background, white text, 8px radius, subtle shadow on hover |
| **Secondary** | Zinc-100 background (dark: zinc-800), 8px radius, no shadow |
| **Ghost** | Transparent, hover shows zinc-100 background |
| **Destructive** | Red-600 background, white text |

Padding: `12px 24px` (py-3 px-6) for default, `8px 16px` for small.

### Cards

- Background: `card` token (white / zinc-900)
- Border: 1px `border` token
- Shadow: None by default (clean, Linear-like)
- Hover: Subtle border color shift to `zinc-300` / `zinc-700`
- Radius: `radius-lg` (8px)
- Padding: `24px` (p-6)

### Badges / Tags

- Shape: **Pill** (radius-full)
- Size: Small text (12px), padding `4px 12px`
- Variants:
  - Default: `muted` background, `muted-foreground` text
  - Primary: `primary` with 10% opacity background, `primary` text
  - Outline: Transparent with `border` stroke

### Recipe Cards (specific)

- Image: Top, 16:9 aspect ratio, `radius-lg` top corners only
- Content padding: `16px`
- Title: `h3` weight, single line with ellipsis
- Meta row: Cook time, difficulty as muted text with icons
- Heart icon: Top-right overlay on image, ghost style
- Hover: Slight scale transform (1.02) with transition

### Form Inputs

- Height: `40px` (h-10)
- Border: 1px `input` token
- Radius: `radius-md` (6px)
- Focus: `primary` ring (2px)
- Placeholder: `muted-foreground`

### Navigation

- Style: Clean horizontal nav, no background color (transparent over page)
- Active state: `primary` color text, subtle underline or background pill
- Mobile: Sheet drawer from left, full-height
- User menu: Avatar dropdown, right-aligned

---

## Dark Mode Implementation

- Applied via `class="dark"` on `<html>` element
- Detected automatically via `prefers-color-scheme: dark`
- No manual toggle in UI (follows system preference)
- All colors defined as CSS variables that swap in `.dark` context

```css
:root {
  --background: 250 250 250; /* zinc-50 */
  --foreground: 24 24 27;    /* zinc-900 */
  /* ... */
}

.dark {
  --background: 9 9 11;      /* zinc-950 */
  --foreground: 250 250 250; /* zinc-50 */
  /* ... */
}
```

---

## Overall Feel

| Attribute | Description |
|-----------|-------------|
| **Density** | Airy and spacious — generous padding, clear visual hierarchy |
| **Contrast** | High contrast text, subtle UI chrome |
| **Motion** | Minimal — subtle hover states, no gratuitous animations |
| **Personality** | Professional, calm, focused — a tool, not a toy |

---

## Mockups

**Figma file:** [Meal Planner — Design Proposal Mockups](https://www.figma.com/design/mPHMd2CLtWRndMijGVPx2w)

- [x] Recipe list (home) — light mode
- [x] Recipe list (home) — dark mode
- [x] Recipe detail page
- [x] Meal plan detail page
- [x] Mobile nav state (closed + open drawer)

---

## Approval

✅ **Approved by owner on 2026-05-03**

**Decisions:**
- Accent color: **Sage (`#7C9082`)**
- Density: **Airy/spacious**
- Mockups: **Figma mockups created and approved**

Phase 1 implementation may now proceed.
