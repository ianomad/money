# Money Beast admin setup

`/admin` is served by this repository. It is not live until the configuration below is saved in Cloudflare and this branch is merged to `main`.

## How the site deploys

- The public site is Cloudflare Pages project `money`.
- `.github/workflows/deploy.yml` runs on a push to `main`: `wrangler pages deploy docs --project-name money`.
- Pages Functions are the `/functions` directory at the repository root (the same place as `functions/_middleware.js`). Do not move them under `docs/`.
- The workflow uploads `docs/` as it is committed. It does not run the Python page builders.
- Merging to `main` deploys. Do not merge until the Google client, secrets, and D1 binding below exist. Until they do, `/admin` fails closed and returns no registry data.

## Google sign-in

The dashboard accepts only a verified Google ID token from the authorization-code flow with PKCE. Email codes, passwords, and Cloudflare Access one-time PINs are not a substitute.

1. In Google Cloud Console, create an OAuth client of type **Web application**.
2. Authorized redirect URI, exactly:

   `https://getmoneybeast.com/admin/auth/callback`

3. If the consent screen is in testing, add the designated admin Google account as a test user.
4. On the Pages project `money`, for **Production**, add these as encrypted secrets (Settings → Variables and Secrets → Encrypt):

   | Name | Value |
   | --- | --- |
   | `GOOGLE_CLIENT_ID` | The web client id |
   | `GOOGLE_CLIENT_SECRET` | The web client secret |
   | `ADMIN_SESSION_SECRET` | At least 32 random characters |
   | `ADMIN_EMAILS` | The designated admin email, and only that email |

   `ADMIN_EMAILS` is a comma-separated allowlist. It is read on the server. It must not be committed, and the browser cannot choose it.

5. Leave `ADMIN_ALLOWED_HOSTS` unset so only `getmoneybeast.com` can start sign-in. Preview hostnames such as `*.pages.dev` stay closed.

A Pages redeploy is required after secrets change. The existing GitHub workflow does that on the next push to `main`.

## Registry database

Registry edits are stored in D1, binding name `ADMIN_DB`. There is no in-memory or browser fallback in production.

1. Create a D1 database in the same Cloudflare account (D1 has a free tier; this does not add a new paid product).
2. Pages project `money` → Settings → Bindings → D1 database binding.
3. Variable name: `ADMIN_DB`.
4. Apply it to Production.
5. Redeploy.

The first signed-in request creates the tables and seeds five repository records (the public site, host redirect, deploy workflow, page builders, and editorial datasets) plus one registry-boundary rule. If `ADMIN_DB` is missing, sign-in can still be attempted but every registry API returns `storage_unconfigured`.

## What a signed-in admin can change

Saving a component or rule updates this dashboard's registry and audit log only. It does not deploy the site, pause a bot, or edit Grok Bot prompts or routines. Metrics are the bundled dataset timestamps plus explicit unavailable adapters for health, job results, evaluations, and usage. They do not include invented traffic or chart history.
