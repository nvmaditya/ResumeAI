# Settings, GitHub cache, theme & app shell

## App shell (authenticated)

**Top header (sticky):**

- **ResumeAI** brand → home list  
- **Resumes** nav  
- **Settings** (opens drawer; not a separate full page in normal use)  
- **Light / Dark** toggle  

**Main:** content area for list or workspace.

**Settings drawer:**

- Right-side panel over a dimmed backdrop.  
- Close via ✕, backdrop click, or Escape.  
- Query `?settings=1` opens it once then cleans the URL (supports `/settings` redirect).

## Settings content

### Account

- Shows **Account: {email}**.  
- Note: **Contact links (LinkedIn, portfolio, phone) live on each resume form — not here.**

### GitHub (for scoring)

**Purpose:** Maintain a **local cache** of public GitHub profile/repo data used when scoring.

**Controls:**

1. **GitHub username** field.  
2. **Save username** — persists profile. Toast: **GitHub username saved**.  
3. **Update GitHub data** — enabled when username non-empty; may save username first, then refresh cache.  
   - Busy: **Updating…**  
   - Success toast: **GitHub cached · N repos**  
   - Failure toast with error.  

**Status lines:**

- Cached: `Cached @user · N repos · {fetched time}`  
- Missing: warning **No cache yet — set username and update.**

**Product rule:** Score reads this cache only—no GitHub API on each score. Users re-run **Update GitHub data** when repos change.

### Log out

Danger full-width **Log out** (see [Auth](./01-auth-and-session.md)).

## Theme

### Modes

- **Light** and **Dark**.  
- Preference stored in the browser.  
- Default if unset: light.

### Toggle behavior

- Available on login, register, and app header.  
- Instantly flips theme tokens (including editor colors on the same tick).  
- Visual **diagonal cover wipe** (~half second) from previous background color, unless user prefers reduced motion (wipe skipped).  
- Toggle disabled while wipe animation is in progress.

### Design personality (for rebuild parity)

- Technical, calm, premium—not playful “SaaS candy”.  
- Accent emerald for primary/score success; amber for proposed edits/warnings; rose for danger/failures.  
- Editor feels like a small IDE; PDF chrome follows theme tokens.

## Toasts

Global lightweight toasts communicate success/failure for create, save, compile, generate, score, coach, versions, GitHub, downloads, etc. Rebuilds should not rely only on silent status lines.

## Health (ops-facing)

`GET /api/v1/health` returns:

- overall status  
- environment name  
- `score_backend`  
- `latex_engine`  
- `coach_backend` / `coach_model` (and related model fields)

Useful for verifying a local install matches expected backends—not a user marketing page.

## Rebuild rules

1. Settings-as-drawer is the primary UX.  
2. GitHub username + explicit cache refresh; score consumes cache only.  
3. Theme light/dark with reduced-motion respect.  
4. Do not move resume contact fields into Settings as the only place to edit them.
