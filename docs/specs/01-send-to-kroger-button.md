# Spec: Send to Kroger Button

**Priority:** High  
**Phase:** 2 — Shopping Experience  
**Type:** Feature  
**Status:** In Progress  

---

## Problem Statement

Users can generate a shopping list from their meal plan, but must manually search for and add each ingredient to their Kroger cart. This breaks the workflow right at the most tedious step — the transition from planning to buying. Since the Kroger OAuth flow, token storage, cart API, and product search API are already implemented, the missing piece is a single button that triggers the full "send list to cart" workflow. Without it, the Kroger integration delivers no real value to the user.

---

## Goals

1. A user can send their entire shopping list to a Kroger cart with one action.
2. The workflow completes without requiring the user to leave the app.
3. Users who are not connected to Kroger are clearly prompted to connect before proceeding.
4. The user receives clear feedback on what was added, what was skipped, and why.
5. The feature works reliably for the target audience of 5–15 users with real shopping lists.

---

## Non-Goals

- **Editing cart contents in-app**: Managing the Kroger cart (removing items, changing quantities) is out of scope — users do that in the Kroger app or website.
- **Partial sends / item selection**: v1 sends the full shopping list. Per-item selection is a future enhancement.
- **Price display**: Showing Kroger prices in the app is out of scope for this version.
- **Order placement**: This feature adds items to the cart only — it does not complete a Kroger purchase.
- **Multi-store support**: Only Kroger is in scope. Walmart, Amazon Fresh, etc. are explicitly not building now.

---

## User Stories

**As a logged-in user with a connected Kroger account**, I want to click a "Send to Kroger" button on my shopping list so that all my ingredients are added to my Kroger cart automatically, saving me from manually searching for each item.

**As a logged-in user without a connected Kroger account**, I want to see a clear prompt explaining that I need to connect my Kroger account before I can use this feature, so I know exactly what to do next.

**As a user whose Kroger token has expired**, I want to be seamlessly re-prompted to reconnect my Kroger account rather than see a confusing error, so that I can complete my grocery send without frustration.

**As a user who has sent their list to Kroger**, I want to see a summary of what was added and what could not be matched so I know what I still need to find myself.

---

## Requirements

### Must-Have (P0)

- **Send button on shopping list page**
  - A "Send to Kroger" button is visible on the shopping list view.
  - The button is only active when the user has a valid Kroger token. If not connected, the button is replaced by or linked to a "Connect Kroger" prompt.
  - Acceptance criteria:
    - [ ] Button appears on the shopping list page for all logged-in users.
    - [ ] Users without a Kroger token see a "Connect Kroger" CTA instead of (or alongside) a disabled button.

- **Trigger cart population**
  - Clicking the button initiates the product matching and cart add workflow for each item on the shopping list.
  - Acceptance criteria:
    - [ ] Clicking the button calls the product matching logic for each shopping list item.
    - [ ] Each matched product is added to the user's Kroger cart via the Cart API.
    - [ ] The button shows a loading/in-progress state while the workflow runs.

- **Result summary**
  - After the workflow completes, the user sees a summary: how many items were added, and how many could not be matched.
  - Acceptance criteria:
    - [ ] Success message shows count of items successfully added to cart.
    - [ ] Unmatched items are listed by name so the user knows what to find manually.
    - [ ] If all items fail, a clear error state is shown (not a silent failure).

- **Token expiry handling**
  - If the Kroger token is expired or invalid at time of send, the user is prompted to reconnect rather than shown a raw error.
  - Acceptance criteria:
    - [ ] A 401 from the Kroger API triggers a re-auth prompt, not an unhandled exception.
    - [ ] After re-auth, the user can retry the send without starting over.

### Nice-to-Have (P1)

- **Per-item status indicators**: Show a checkmark or ❌ next to each shopping list item after the send, indicating whether it was matched and added.
- **Retry for failed items**: Allow the user to retry just the items that failed to match, without resending the whole list.
- **"Open Kroger Cart" link**: After a successful send, provide a direct link to the user's Kroger cart so they can review it immediately.

### Future Considerations (P2)

- **Selective send**: Let users choose which items to send (e.g., uncheck pantry staples they already have).
- **Quantity editing**: Allow users to adjust quantities before sending.
- **Send history**: Log past sends so users can see what was sent on a given date.

---

## Success Metrics

**Leading indicators (days to weeks post-launch):**
- "Send to Kroger" button is clicked on ≥50% of shopping lists that are generated.
- End-to-end success rate (items matched + added to cart) ≥70% of items per send.
- Zero silent failures — every send attempt results in visible feedback to the user.

**Lagging indicators (weeks to months post-launch):**
- Anecdotal feedback from the 5–15 users that shopping trips feel faster.
- Reduction in "I had to manually search for everything" complaints.

---

## Open Questions

| Question | Owner | Blocking? |
|---|---|---|
| What is the current product matching strategy — fuzzy name search, exact UPC, or something else? This affects how many items we expect to match. | Engineering | Yes — needed before estimating success rate |
| Should unmatched items be shown inline on the shopping list, or in a modal/toast? | Andre (design preference) | No |
| Is there a Kroger API rate limit that could affect sends for larger shopping lists (20+ items)? | Engineering | No — but good to know before launch |
| Should the button be disabled after a successful send to prevent double-adds, or should re-sends be allowed (e.g., after updating the meal plan)? | Andre | No |

---

## Timeline Considerations

- This feature is **in progress** (Phase 2) and is a direct dependency of the Product Matching feature — the two should be built together or in close sequence.
- No hard external deadlines. Ship when matching works well enough to be useful.
- Suggested sequencing: Store Location Selection → Product Matching → Send to Kroger Button (so the user's preferred store is known before matching runs).
