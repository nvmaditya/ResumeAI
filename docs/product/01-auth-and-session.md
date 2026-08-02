# Auth & session

## Purpose

Give each user a private workspace: their resumes, versions, score jobs, and GitHub cache are scoped to their account. There is **no** third-party OAuth login in the shipped product—only email + password.

## Register

**Where:** `/register` (public).

**What the user does:**

- Enters **email** and **password**.
- Password must be at least **8 characters** (enforced in the form).
- Submits **Create account**.

**What happens:**

- Account is created if the email is free.
- On success the app **logs the user in immediately** (register then login) and sends them to the resumes list.
- On failure (e.g. email already registered), an error message appears on the form; the user stays on register.

**Empty / error behavior:**

- Required fields; busy state **Creating…** while the request runs.
- Link to **Log in** if they already have an account.

## Login

**Where:** `/login` (public).

**What the user does:**

- Enters email + password → **Continue**.

**What happens:**

- Valid credentials return a session **access token** stored in the browser.
- User is navigated to **/** (resumes list).
- Invalid credentials show an alert-style error (**Invalid credentials** or equivalent API message).

**Also on this screen:**

- Brand mark **ResumeAI**, short value copy.
- **Light / Dark** theme toggle (same theme system as the rest of the app).
- Link to **Create one** (register).

## Session & protected routes

**Rule:** Any main app route under the authenticated shell requires a token.

- Without a token, the app redirects to **Login**.
- Authenticated shell includes: resumes list, resume workspace, settings drawer.
- Legacy path `/settings` redirects into the list with settings opened (`/?settings=1`).

**API usage pattern (product-level):**

- Authenticated calls send the bearer token.
- A 401 / “Not authenticated” on resume list load sends the user back to login.

## Logout

**Where:** Settings drawer → **Log out**.

**What happens:**

- Token is cleared.
- Settings closes.
- User is sent to **Login**.

There is no separate “sessions list” or remote revoke UI in the MVP.

## Profile fields related to auth

- **Email** is the account identity; shown read-only in Settings as “Account: …”.
- Editable profile pieces used in-product today center on **GitHub username** (see [Settings & GitHub](./10-settings-github-theme.md)). Display name / headline fields may exist in the data model but are not the primary Settings UX.

## Rebuild rules

1. Free email+password auth with JWT (or equivalent bearer session) is enough—no external IdP required for MVP parity.
2. Register → automatic login is expected UX.
3. Minimum password length **8** must remain visible and enforced.
4. All resume/score/coach/settings data must remain **user-owned**; no shared anonymous workspace.
