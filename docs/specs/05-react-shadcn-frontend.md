# Spec: React + shadcn/ui frontend migration

**Priority:** Medium
**Phase:** 4 — Polish
**Type:** Architecture / redesign
**Status:** Ready for Development

---

## Problem Statement

The current UI is Flask-rendered Jinja2 templates with hand-rolled CSS. It works but is slow to iterate on, has inconsistent component styling across pages, and offers no path to richer interactivity without increasingly awkward JavaScript sprinkled into templates. Adopting shadcn/ui as a React frontend gives the app a polished, consistent design system, proper component architecture, and dark mode — while keeping Flask and the .NET API as the data layer underneath.

---

## Goals

- Every page in the app is rebuilt as a React component using shadcn/ui primitives
- The design is a complete clean break from the existing UI — no inherited colours, spacing, or patterns
- A new design language is proposed and agreed on before implementation begins: colour palette, typography, spacing scale, and component personality
- The result feels sleek, intuitive, and polished — low visual noise, high ease of use
- Dark mode follows the user's system preference automatically
- Flask becomes a pure JSON API — no more server-rendered HTML
- The migration is structured in phases so the app remains usable throughout

---

## Non-Goals

- Switching from Flask-Login session auth to JWT tokens — sessions stay, exposed via an API endpoint
- Migrating the .NET API — it stays unchanged
- Building a mobile app or PWA (separate backlog item)
- Offline support
- Carrying over any element of the existing visual design — this is a clean break

---

## Design Language (to be proposed before Phase 1 begins)

Before any code is written, the implementing agent must propose a complete design system for review. The existing design is fully discarded. The new design should feel like a modern, minimal food/lifestyle app — think Linear or Vercel's aesthetic applied to cooking.

The proposal must cover:

**Colour palette**
- A primary accent colour (not the old green) — propose 2–3 options with rationale
- Neutral scale for backgrounds, surfaces, borders, and text
- Semantic colours for success, warning, error states
- All colours must work in both light and dark mode using Tailwind CSS variables

**Typography**
- Font family (suggest a clean sans-serif — Geist, Inter, or similar available via Google Fonts or Fontsource)
- Type scale: heading sizes, body, small/muted, labels
- Font weights in use (recommend limiting to 2–3)

**Spacing and layout**
- Base unit (recommend 4px)
- Card corner radius (recommend generous rounding — 12–16px)
- Content max-width and page padding

**Component personality**
- Buttons: filled primary, outline secondary, ghost tertiary — propose border radius and padding
- Cards: subtle shadow or border? Hover state?
- Badges/tags: pill or rectangular?
- Overall feel: airy and spacious vs compact and dense?

**Deliverable:** before writing any React or Tailwind code, output a design proposal as a markdown section or comment for the owner to approve. Proceed to Phase 1 implementation only after the design direction is confirmed.

---

## Target Stack

| Layer | Technology |
|---|---|
| Frontend framework | React 18 + TypeScript |
| Build tool | Vite |
| Component library | shadcn/ui |
| Styling | Tailwind CSS v3 (bundled with shadcn) |
| Routing | React Router v6 |
| Server state | TanStack Query (React Query) |
| Auth state | React Context + `/api/auth/me` |
| Backend | Flask (JSON API only, no templates) |
| Data | .NET API (unchanged) + SQLite via Flask |

---

## New Project Structure

```
meal-planner/
├── frontend/               ← new React app
│   ├── src/
│   │   ├── components/     ← shadcn/ui + shared components
│   │   ├── pages/          ← one file per route
│   │   ├── lib/            ← API client, auth context, utils
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── web/                    ← Flask JSON API only (no templates folder)
│   ├── app.py
│   ├── auth.py
│   └── kroger.py
```

---

## Pages to Migrate (19 templates → React pages)

| Current template | React page | Route |
|---|---|---|
| `index.html` | `RecipeList` | `/` |
| `recipe.html` | `RecipeDetail` | `/recipe/:id` |
| `search.html` | `Search` | `/search` |
| `search_advanced.html` | `SearchAdvanced` | `/search/advanced` |
| `meal_plans_list.html` | `MealPlanList` | `/meal-plans` |
| `meal_plan_detail.html` | `MealPlanDetail` | `/meal-plans/:id` |
| `create_meal_plan.html` | `CreateMealPlan` | `/meal-plans/create` |
| `shopping_list.html` | `ShoppingList` | `/meal-plans/:id/shopping-list` |
| `meal_prep.html` | `MealPrepGuide` | `/meal-plans/:id/meal-prep` |
| `settings.html` | `Settings` | `/settings` |
| `import_recipe.html` | `ImportRecipe` | `/admin/import-recipe` |
| `pending_deletions.html` | `PendingDeletions` | `/admin/pending-deletions` |
| `admin_ai_tagging.html` | `AiTagging` | `/admin/ai-tagging` |
| `admin_recipe_quality.html` | `RecipeQuality` | `/admin/recipe-quality` |
| `admin_invites.html` | `InviteAdmin` | `/admin/invites` |
| `access_denied.html` | `AccessDenied` | `/access-denied` |
| `invite_invalid.html` | `InviteInvalid` | `/invite/invalid` |

---

## Requirements

### Phase 0 — Design proposal (gate before any development begins)

**Deliverable: design spec document**

Before writing any React, Tailwind, or shadcn/ui code, produce a written design proposal covering the full design language defined in the Design Language section above. Output as a markdown file at `docs/specs/05a-design-proposal.md`.

The document must include:
- Proposed colour palette with hex values for light and dark modes
- Font family selection with rationale
- Type scale (h1–h4, body, small, muted)
- Spacing and layout rules
- Component personality decisions (button styles, card treatment, badge shape, etc.)
- At least 2–3 alternative accent colour options with a recommended pick and reasoning

This document is a gate — do not proceed to Phase 1 until the owner has reviewed and approved it.

Acceptance criteria:
- [ ] `docs/specs/05a-design-proposal.md` exists and covers all design language items
- [ ] Owner has reviewed and left approval or revision feedback before Phase 1 begins

**Deliverable: Figma mockup (optional but recommended)**

If Figma MCP is available, create a Figma file with high-fidelity mockups of the following key screens using the proposed design language:
- Recipe list (home page) — light and dark mode
- Recipe detail page
- Meal plan detail page
- Mobile nav state

The Figma file allows the owner to comment inline on specific design decisions before any code is written. Share the Figma link in `docs/specs/05a-design-proposal.md`.

If Figma MCP is not available, produce annotated HTML/CSS mockups of the same screens as static files in `docs/design-mockups/` and open them in the browser for review.

Acceptance criteria:
- [ ] Key screens are mocked up at high fidelity in Figma or as static HTML
- [ ] Owner has reviewed mockups and provided feedback or approval
- [ ] Any feedback is incorporated into `05a-design-proposal.md` before Phase 1 begins

---

### Phase 1 — Foundation (prerequisite for all other phases)

**React project scaffold in `frontend/`**
- `npm create vite@latest frontend -- --template react-ts`
- shadcn/ui initialised with the colour palette and tokens from the approved design proposal (see Design Language section)
- React Router v6 and TanStack Query installed
- Acceptance criteria:
  - [ ] `npm run dev` serves the app at `localhost:5173`
  - [ ] shadcn/ui `Button` and `Card` components render correctly
  - [ ] Dark mode toggles via `class="dark"` on `<html>` driven by `window.matchMedia('prefers-color-scheme: dark')`

**Flask API refactor — all routes return JSON under `/api/`**
- Every Flask route currently returning HTML is converted to return JSON
- All routes prefixed with `/api/`
- New endpoints required:
  - `GET /api/auth/me` — returns `{id, name, email, avatar_url, is_admin}` or 401
  - `GET /api/recipes` — list with optional `?q=`, `?favorites=1`, `?tag=`
  - `GET /api/recipes/:id` — recipe detail with ingredients, instructions, tags, allergens, `is_favorited`
  - `GET /api/meal-plans` — proxies .NET API scoped to current user
  - `GET /api/meal-plans/:id` — proxies .NET API
  - `GET /api/meal-plans/:id/shopping-list` — proxies .NET API
  - `GET /api/meal-plans/:id/meal-prep` — proxies .NET API
  - `GET /api/settings` — returns current user preferences
  - `POST /api/settings` — saves preferences
  - All existing admin endpoints under `/api/admin/`
- Acceptance criteria:
  - [ ] All `/api/` endpoints return `Content-Type: application/json`
  - [ ] CORS configured for `localhost:5173` in development only
  - [ ] 401 returned for all protected endpoints when unauthenticated
  - [ ] Vite proxy configured in `vite.config.ts` to forward `/api` and `/auth` to `localhost:5001`

**Auth flow**
- Google OAuth flow stays in Flask at `/auth/login` and `/auth/google/callback`
- After successful OAuth, Flask sets session cookie and redirects to React app root (`/`)
- React `AuthContext` calls `GET /api/auth/me` on mount to hydrate auth state
- `ProtectedRoute` wrapper redirects unauthenticated users to `/auth/login`
- `AdminRoute` wrapper redirects non-admins to `/`
- Acceptance criteria:
  - [ ] Clicking "Sign in" in React redirects to Flask OAuth, returns to React home after login
  - [ ] `useAuth()` hook returns current user or null
  - [ ] Page refresh preserves auth state via session cookie
  - [ ] Logout calls `/auth/logout` and clears React auth state

**Flask serves React build in production**
- Vite builds to `frontend/dist/`
- Flask serves `frontend/dist/index.html` as a fallback for all non-`/api/` non-`/auth/` routes
- Flask serves `frontend/dist/assets/` as static files
- Dockerfile updated with a Node build stage
- Acceptance criteria:
  - [ ] `npm run build` produces a working `dist/`
  - [ ] Flask SPA fallback serves React app for all client-side routes
  - [ ] Docker image builds and serves the app correctly end-to-end

**`AppShell` layout component**
- Top nav with logo, nav links (Recipes, Meal Plans, Search), user avatar + dropdown (Settings, Sign out)
- Admin links (Import, Pending Deletions, AI Tagging, Invites) shown only when `user.is_admin`
- Dark mode applied on mount via system preference; no manual toggle needed
- Uses: shadcn `NavigationMenu`, `Avatar`, `DropdownMenu`, `Sheet` (mobile nav)
- Acceptance criteria:
  - [ ] Responsive — hamburger drawer on mobile
  - [ ] Dark mode applies automatically on page load
  - [ ] Admin nav links hidden for non-admin users

### Phase 2 — Core pages

**`RecipeList` (`/`)**
- Responsive card grid (1 / 2 / 3–4 cols) using shadcn `Card`
- Each card: image, name, tag badges, cook time, difficulty, heart toggle
- Favorites filter pill above the grid
- Skeleton loading state while fetching
- Fetches `GET /api/recipes`
- Acceptance criteria:
  - [ ] Favorites filter updates the list without page reload
  - [ ] Heart toggle updates optimistically

**`RecipeDetail` (`/recipe/:id`)**
- Hero image, title, stats grid, nutrition panel, ingredients list, step-by-step instructions
- Action bar: Print, Delete, Add to Cart, Add to Meal Plan
- Ratings + notes panel (from spec 02) when authenticated
- shadcn `Toast` for cart/plan action feedback
- Acceptance criteria:
  - [ ] Print stylesheet hides action bar and nav
  - [ ] Action bar buttons call API and show toast on success/error

**`Search` and `SearchAdvanced`**
- Debounced search input (300ms), results update in place
- Advanced: filter by tag, difficulty, cook time range, has-image toggle
- URL params updated on filter change for shareability
- Acceptance criteria:
  - [ ] URL params reflect active filters and survive page reload

**`MealPlanList`, `MealPlanDetail`, `CreateMealPlan`**
- List: cards per plan (name, date range, recipe count, actions)
- Detail: recipe list, stats, links to shopping list and meal prep
- Create: name + date picker + multi-select recipe picker
- Acceptance criteria:
  - [ ] Create form validates required fields before submit
  - [ ] Detail page data from .NET API via `/api/meal-plans/:id`

**`ShoppingList` and `MealPrepGuide`**
- Shopping list: aisle-grouped items, checkboxes, print button
- Meal prep: step list
- Acceptance criteria:
  - [ ] Checked items persist in component state during the session
  - [ ] Print view hides nav and chrome

### Phase 3 — Admin + remaining pages

- `Settings` — Kroger OAuth connect/disconnect, preferences
- `ImportRecipe` — URL scrape + preview + save
- `PendingDeletions`, `RecipeQuality`, `AiTagging`, `InviteAdmin` — behind `AdminRoute`
- `AccessDenied`, `InviteInvalid` — no nav, unauthenticated-safe

### Phase 4 — Cleanup

- Delete `web/templates/` folder
- Delete `web/static/style.css`
- Remove all `render_template` calls from `app.py`
- Update `fly.toml` if build command changes
- Update CI/CD pipeline (spec 06) to include `npm run build`

---

## shadcn/ui Components Required

`Button`, `Card`, `Badge`, `Input`, `Select`, `Textarea`, `Toast` / `Sonner`, `Dialog`, `NavigationMenu`, `Avatar`, `DropdownMenu`, `Checkbox`, `Separator`, `Skeleton`, `Sheet` (mobile drawer), `DatePicker`, `Command` (recipe multi-select)

---

## Technical Notes

**CORS:** Flask-CORS allows `http://localhost:5173` in development only. In production, React is served by Flask so no CORS header is needed.

**Vite proxy (`vite.config.ts`):**
```ts
server: {
  proxy: {
    '/api': 'http://localhost:5001',
    '/auth': 'http://localhost:5001',
    '/kroger': 'http://localhost:5001',
  }
}
```

**TanStack Query key conventions:** `['recipes']`, `['recipe', id]`, `['meal-plans']`, `['meal-plan', id]` — consistent keys ensure correct cache invalidation after mutations.

**Dockerfile build stage:**
```dockerfile
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
# ... existing Python setup ...
COPY --from=frontend-build /frontend/dist ./web/static/dist
```

**Branch strategy:** Phase 1 temporarily breaks the app until the SPA fallback is wired. Do all of Phase 1 on a feature branch (`feat/react-frontend`) and merge only when the shell + auth flow is fully working end-to-end.

---

## Success Metrics

- All 17 pages render correctly in both light and dark mode
- No Jinja2 templates remain after Phase 4 cleanup
- Lighthouse performance score ≥ 80 on the recipe list page
- Zero regressions on auth, favorites, Kroger cart, and meal plan flows

---

## Open Questions

- **[Product]** ✅ Resolved — existing design is fully discarded. Implementing agent must propose a new design language for approval before writing any UI code (see Design Language section above).
- **[Engineering]** The .NET API runs on a separate port. In production on fly.io, are both services on the same internal host or separate apps? Investigate and choose the correct proxy strategy before implementing `/api/meal-plans` routes.
- **[Engineering]** Phase 1 is a breaking change to all Flask routes. Use a feature branch (`feat/react-frontend`) and merge only when the shell + auth flow works end-to-end.
