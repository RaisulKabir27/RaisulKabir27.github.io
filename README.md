# Raisul Kabir News · Academic Portfolio

A single-page, mobile-first portfolio with light and dark themes. The theme switch is in the header; the page follows the visitor's system setting until they choose. Everything the page needs (styles, scripts, icons, photo and university logos) is inside `index.html`, so it works on GitHub Pages and when opened straight from disk.

The hero contains a small interactive demo (Build, Challenge, Verify, Trust) drawn in SVG with plain JavaScript: no libraries, no tracking, and it pauses whenever it is off screen. It works with a mouse, touch or keyboard, and with reduced motion.

```
index.html                         the whole site
RaisulKabirNews_CV.pdf             linked by both "Download CV" buttons
assets/img/                        TechShoi logo
data/scholar.js                    citation numbers, refreshed automatically
scripts/update_scholar.py          fetches Google Scholar metrics (not published)
analytics/                         private analytics server and dashboard (not published; see analytics/README.md)
.github/workflows/deploy.yml       Scholar refresh every 6 hours + GitHub Pages deploy
.nojekyll                          serve files as-is
```

## Links to fill in

Search `index.html` for `Embed Link`. Each comment sits right above the line to edit:

- **Analytics server:** after setting up `analytics/`, put its address in `<meta name="analytics-endpoint" content="">`. While it's empty, the site sends nothing.
- **HAR paper:** optional preprint or submission link.
- **Page head:** your live site URL (`og:url`, `canonical`) and an optional 1200×630 preview image.

## Preview locally

```bash
cd path/to/this/folder
python3 -m http.server 8000
# open http://localhost:8000
```

Opening `index.html` directly also works. Analytics never runs locally.

## Deploy on GitHub Pages

1. Push these files to the `main` branch of your `RaisulKabir27.github.io` repository.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. **Settings → Actions → General → Workflow permissions: Read and write permissions.**
4. Open the **Actions** tab, choose **Refresh Scholar stats and deploy site**, then **Run workflow**.

Every push to `main` redeploys. The workflow also checks Google Scholar every 6 hours and redeploys only when the numbers change.

The workflow publishes only `index.html`, the CV, `.nojekyll`, `assets/` and `data/`. If you add another public file (for example a preview image), add it to the "Collect the public website files" step in `.github/workflows/deploy.yml`.

## Citation count

Browsers can't read Google Scholar from another website (Google blocks it), so the workflow fetches your profile every 6 hours and writes `data/scholar.js`; the page reads that file.

- If Google blocks the request from GitHub's servers (the run shows a warning), add a free [SerpAPI](https://serpapi.com) key as a repository secret named `SERPAPI_KEY`.
- You can also type the number into `data/scholar.js` (`"citations": 12,`) yourself. A failed fetch never overwrites it; a successful one replaces it with the live value.
- GitHub pauses scheduled workflows after 60 days without repository activity. Re-enable it from the Actions tab if that happens.

## Visitor statistics

See `analytics/README.md`. In short: a free Cloudflare Worker stores anonymous, aggregate statistics. It uses no cookies, stores no IP addresses and does no fingerprinting, and only you can see the results, on a password-protected dashboard. Open your site once with `#analytics-off` on each of your own devices so your visits aren't counted.
