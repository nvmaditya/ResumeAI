# Auth & session

## Purpose

Private workspace per user: resumes, versions, score jobs, and GitHub cache are owned by the account. **No** third-party OAuth login in the shipped product.

## Mode / availability

Public routes: `/login`, `/register`. Everything under the app shell requires a session token.

## User controls

| Control | Where | Does |
|---------|-------|------|
| Email + password | Register / Login forms | Create account or sign in |
| Create account | Register | Register then **auto-login** → Resumes |
| Continue | Login | Store token → Resumes |
| Light / Dark | Auth screens | Theme toggle (same system as app) |
| Log out | Settings drawer | Clear token → Login |
| Create one / Log in links | Auth footers | Navigate between register and login |

## Happy path

1. Register with email + password (**≥ 8** characters, shown and enforced).  
2. On success: immediate login, land on **Your resumes**.  
3. Later visits: Login → Resumes.  
4. Log out from Settings when done.

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| Register success | Resumes list; session active |
| Email already registered | Inline error; stay on register |
| Login bad credentials | Inline error (e.g. invalid credentials); stay on login |
| Login success | Navigate home |
| No token on protected route | Redirect to Login |
| 401 on resume list | Redirect to Login |
| Busy submit | Button **Creating…** / **Signing in…** |

## Hard rules

1. Free email+password + bearer session is enough for MVP parity.  
2. Register → automatic login is expected.  
3. Minimum password length **8**.  
4. Data is user-scoped (no shared anonymous workspace).

## Done check

- [ ] Public auth pages with theme toggle  
- [ ] Protected shell redirects without token  
- [ ] Logout clears session  
