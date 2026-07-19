# AEGIS dashboard deployment root

GitHub Pages publishes this directory from `master` → `/docs`.

Workflow:

1. Edit the canonical site in `dashboard/`.
2. Mirror `dashboard/index.html`, `dashboard/app.js`, `dashboard/styles.css`, and `dashboard/data/schedule.json` into this directory.
3. Validate both copies.
4. Push the reviewed commit to `master`.
5. Wait for the Pages build and inspect the live URL.

The dashboard is status-only. Local-ready does not mean uploaded, and performance placeholders must remain empty until platform analytics return real data.
