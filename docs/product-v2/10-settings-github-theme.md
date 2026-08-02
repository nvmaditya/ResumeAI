# Settings, GitHub cache, theme & app shell

## App shell

| Element | Does |
|---------|------|
| ResumeAI brand | Home list |
| Resumes | Nav home |
| Settings | Open right drawer |
| Light / Dark | Theme toggle |
| `?settings=1` | Open drawer once, clean URL |
| Escape / backdrop / ✕ | Close settings |

## Settings content

### Account

- Read-only email.  
- Copy: contact links live on **each resume form**, not here.

### GitHub (for scoring)

| Control | Does |
|---------|------|
| GitHub username | Profile field |
| Save username | Persist; toast saved |
| Update GitHub data | Refresh local cache (may save username first) |

Status: cached @user · N repos · time **or** warning no cache yet.

### Log out

Clears session → Login.

## Theme

- Light / dark; stored in browser; default light.  
- Instant token flip (editor same tick).  
- Diagonal wipe unless `prefers-reduced-motion`.  
- Toggle disabled during wipe.

Design: technical, calm; emerald accent; amber for proposals; rose for danger.

## Health (ops)

`GET /api/v1/health` → status, env, score_backend, latex_engine, coach_backend/model.

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| Save username | Toast |
| Update GitHub success | Cached · N repos toast |
| Update fail | Error toast |
| No username | Update disabled / error path |
| Theme toggle | Wipe (or instant if reduced motion) |

## Hard rules

1. Settings-as-drawer primary UX.  
2. Explicit cache refresh; score reads cache only.  
3. Theme + reduced-motion.  
4. Contacts on resume form.

## Rebuild check

- [ ] Cache status visible  
- [ ] Score does not require live GitHub  
