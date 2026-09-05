# Website Clone Report — Amine Portfolio

**Source (live):** https://amine-portfolio-3d.onrender.com/
**Clone location:** this folder (`amine-portfolio-clone/`)
**Clone date:** 2026-09-05

---

## 1. How to run the clone

The site must be served over HTTP (ES modules + WebGL do not work from `file://`):

```bash
cd amine-portfolio-clone
python3 -m http.server 8080
# open http://localhost:8080/
```

Any static server works (npx serve, nginx, caddy…). Serve the folder **as the site root**.

---

## 2. What the original is built with (recon findings)

| Aspect | Finding |
|---|---|
| Builder / framework | **Framer** (`meta generator: Framer ad1bd2b`, "Made in Framer") — React SSR + hydration runtime |
| Hosting | onrender.com (Framer publishing) |
| Pages | **Single page** — all nav links are anchors (`#home #about #stack #services #projects #contact`). A `searchIndex` JSON lists 39 CMS pages (e.g. `/bookease-website-in-framer`) but every one returns **404 live** — orphaned template entries, not linked from the homepage, so not part of the site. |
| Styling | 100% inline `<style>` blocks in the HTML (breakpoint CSS + SSR CSS) — no external stylesheets |
| JS runtime | 14 ES-module chunks on `framerusercontent.com` (react, motion/framer-motion, framer runtime, site code) |
| Fonts | Public Sans + PT Mono (Google Fonts, woff2), plus 37 custom Framer-uploaded woff2 fonts |
| 3D content | **Spline** "Nexbot robot character concept" embed (`my.spline.design`), runtime loaded from unpkg (`@splinetool/runtime@1.9.98` + wasm packages) |
| Icons | Phosphor Icons + Material Icons loaded as **dynamically imported modules** (`framer.com/m/...`) |
| Analytics | Framer events (`events.framer.com`) — see §5 |

## 3. Extraction methods used

1. **Raw SSR HTML** fetched with curl — used as the clone's `index.html` (chosen over the post-hydration DOM so that React hydration works identically to live, keeping all Framer scroll/appear animations functional).
2. **Headless-browser recon** (desktop 1440px + mobile 390px): rendered DOM capture, full network-request log, and screenshots — used to discover assets that never appear in the HTML: 4 icon modules, Spline runtime files, editor-bar assets.
3. **Recursive asset mirror** (Python script): every URL in the HTML → downloaded → each downloaded JS/JSON scanned for more URLs → repeat until fixpoint. 133 files pulled from `framerusercontent.com`, `fonts.gstatic.com`.
4. **Spline scene capture**: the embed page at `my.spline.design` is fully self-contained (scene data embedded in its 4.8 MB HTML, no external scene file). It was downloaded wholesale plus its 8 runtime/wasm dependencies from unpkg, making the 3D robot **fully local** — no Spline account/server needed.
5. **URL rewriting** with per-file relative-path resolution:
   - HTML: all CDN URLs → `./assets/…`, Spline iframe → `./spline/index.html`
   - JS chunks: CDN URLs → chunk-relative paths; dynamic icon-import bases patched to local dirs (icon files renamed to include their `@version` suffix, which the runtime appends)
   - Spline runtime: wasm fetch bases patched to local package dirs; blob-worker bases patched via `new URL(…, import.meta.url)` so they stay absolute and worker-safe
   - Framer's Embed component was patched (2 conditions) to accept **relative iframe URLs** — it otherwise force-prefixes `https://` and would break the local Spline embed after hydration.
6. **Stripped (intentional):** Framer analytics script tag (`events.framer.com/script`) and the editor-bar preload snippet (`framer.com/edit/init.mjs`).

## 3b. Post-delivery fixes (CTA hover icons + full offline hardening)

After the first delivery, the hover icons inside the black circles of the three CTA buttons ("Let's Work Together! / Contact Me", "Read My CV", "Book a Call") were found missing. Root cause was a 3-part failure chain, now fully fixed:

1. **Wrong MIME type** — icon wrapper files were named `Name.js@0.0.57`; static servers don't recognize that extension and served `application/octet-stream`, which browsers **refuse to execute** as an ES module. Fix: renamed to plain `Name.js` and patched the two import templates in the chunks that appended the `@version` suffix.
2. **Icon React modules never downloaded** — the wrappers re-export from `framerusercontent.com/modules/<hash>/<hash>/Name.js`; those 4 files were missing. Fix: downloaded into `assets/modules/<hash>/<hash>/` and corrected the wrappers' relative import paths (`../../modules/...`).
3. **Framer editor-bar runtime injection** — a chunk dynamically imported `framer.com/edit/init.mjs`, pulling remote editor UI at runtime. Fix: repointed to a local no-op stub (`assets/modules/editorbar-stub.js`).

Offline hardening (second pass):
- Downloaded ~60 fonts the JS font-loader references (Public Sans/PT Mono/Inter subsets, incl. Inter Bold/Italic variants recovered from `app.framerstatic.com` after the `framerusercontent.com/assets/` originals returned 403).
- Downloaded **13 lazy-loaded chunks** (Google/Fontshare font metadata loaders + code-split section components) that were never captured and could 404 at runtime.
- The Spline scene embeds a text object using PT Mono; the Spline runtime constructs a Google Fonts URL at runtime. Fix: patched `addFont()` in the Spline runtime + injected tiny fetch shims in **both** documents (main page + spline iframe) redirecting any `fonts.gstatic.com` fetch to the local mirror. Draco decoder files also mirrored.

**Final state: zero network requests leave the machine — the folder is 100% self-contained.**

## 3c. Post-delivery fix 2 — "Read My CV" button now opens/downloads the CV

On the original site the floating "Read My CV" pill was a template leftover: it linked to `https://original-shares-496620.framer.app/#contact` (the Framer template's contact section — not a CV at all). Per owner request it now behaves like the "Download CV" button:

- `index.html`: anchor href → `./assets/fonts/framer/k7B2UWJqox32vTOmGRtWHQ53G4.pdf` with `download="" target="_blank" rel="noopener"` (same attributes as the "Download CV" button).
- React chunk `bQpuC35cZzF-…DN4wskZc.mjs`: the component's link prop (`bGXKran9l`) patched to the same local PDF, so hydration/re-render cannot revert the link.
- The CV file is the exact same PDF the "Download CV" button serves (226 KB, valid PDF 1.4).
- Everything else on the button — label, ReadCvLogo hover icon in the black dot, animations — untouched.

Patch script: `scripts/fix_cv_link.py` (idempotent, with context assertions). SEO `canonical` / `og:url` meta tags were intentionally left untouched.

## 3d. Post-delivery fix 3 — Services section reduced from 9 slides to 5 (3D/product-ads focus)

Per owner request, the Services scroll-story now shows **5 slides** aimed at a 3D designer profile:

| # | Slide | 3D shape | Source |
|---|---|---|---|
| 01 | **3D Product Ads** | Red Pyramid | retitled + new copy (was "Web Design & Development") |
| 02 | Landing Page Design | Blue Cube | kept as-is |
| 03 | **Product Visualization** | Green Cylinder | retitled + new copy (was "UI/UX Prototyping" + duplicate "Responsive Design") |
| 04 | Branding & Visual Identity | Yellow Heart | kept (renumbered 06→04) |
| 05 | 3D & Motion Design | Blue Gem | kept (renumbered 08→05) |

Removed (hidden): Web Design & Development copy, duplicate "Responsive Design" card, Design Systems & UI Kits, Performance Optimization, Maintenance & Support.

Implementation (hydration-proof): slides 4/5/7/9 are hidden via a small `<style id="clone-services-five">` block using their stable Framer classes (`display:none!important`) — the classes exist in the compiled chunks too, so the hiding survives any React re-render. Every changed text was patched in **both** `index.html` and the React chunk `bQpuC35cZzF-*.mjs` (default children + variant maps + slide numbers). The removed slides' DOM/strings remain but are never visible; the section height is `min-content`, so no scroll gaps. Patch script: `scripts/fix_services_5.py` (idempotent).

Verification (`scripts/verify_services_5.py`): desktop 1440px — 5/9 descriptions + 5/8 shapes visible, zero stale texts; mobile 390px — number cards 01–05 visible, 06–09 absent; 0 console errors, 0 failed/external requests. Screenshots: `verification/services5_desktop_slide1.png`, `services5_desktop_slide5.png`, `services5_mobile.png`. Note: the template renders slide titles and descriptions as one concatenated paragraph (e.g. "…AdsAds that stop…"), faithfully preserved.

## 3e. Post-delivery fix 4 — sticky Services number card now switches 01→05 while scrolling

On desktop the Services section has one sticky card (huge 200px number + title) that must switch as each slide crosses 50% of the viewport. After fix 3 (hiding slides 4/5/7/9) the card stayed stuck at "01": Framer's variant-switcher HOC (`Ww` in `framer.C0HxxWDg.mjs`) measures **all nine** scroll-target divs to build an interpolation range; the four `display:none` targets measure at Y=0, making the range non-monotonic, so the index lookup never resolved and the variant fell back to the default.

Fix (`scripts/fix_services_number_scroll.py`, idempotent): rewrote the `__framer__targets` array in chunk `bQpuC35cZzF-*.mjs` to only the five visible slides' targets — `01 (oe)`, `02 (M)`, `03 (N)`, `06→04 (L)`, `08→05 (se)`. The five visible trigger divs are exactly 900px apart, so the range is monotonic and the card now steps 01→02→03→04→05 with matching titles (3D Product Ads → Landing Page Design → Product Visualization → Branding & Visual Identity → 3D & Motion Design). Verified by real-scroll Playwright run (`scripts/verify_number_scroll.py`): all five states + scroll-back correct, 0 console errors, 0 external requests.

## 3f. Post-delivery addition — self-hosted media gallery in the Projects tab (from Google Drive)

Per owner request, all media from Drive folder `1sfaNY-nfHA6Ol5-pWCHXdJ_opH8OeIxf` was imported into a gallery that lives **inside the existing Projects section** (between the "CLICK HER" Behance placeholder and the footer CTA), reachable from the existing **Projects** nav tab — no nav/menu changes. Full details in `GALLERY_REPORT.md`. Summary: 16 Drive files (4 categories: animation / cgi / environment / products-ads) → deduped, videos transcoded H.264 mp4 (long edge 1280, faststart, posters generated), photos re-encoded WebP (1600px + 800px thumbs) — **530 MB → 41 MB**, fully self-hosted (`assets/gallery/`). Vanilla-JS grid (`.gp-*` namespaced, injected post-hydration so React/Framer hydration is untouched), filter pills in nav style (orange `#f94706` active), lazy-loaded tiles with aspect-ratio placeholders (zero layout shift), and a lightbox with keyboard navigation that loads each video **only on click**. 22-point Playwright verification passed (desktop/tablet/mobile, filters, lightbox, hydration-safety resize test, 0 console errors / 0 external / 0 failed requests). Screenshots: `verification/gallery_*.png`.

## 4. Verification results (clone vs live)

- **Requests:** full load + complete scroll — **0 failures, 0 404s, 0 external requests** (audited in fresh Chromium sessions at 1440px and 390px).
- **Console:** no errors.
- **CTA hover icons:** all 3 mounted and rendered on hover, verified pixel-identical to the live site — ↓ ArrowDown ("Let's Work Together!"), ReadCvLogo ("Read My CV"), Phone ("Book a Call") — see `verification/` screenshots.
- **"Read My CV" click behavior (fix 2):** post-hydration DOM keeps `href=./assets/fonts/framer/k7B2UWJqox32vTOmGRtWHQ53G4.pdf` + `download` + `target=_blank`; clicking downloads a verified `%PDF-` file (226,356 bytes); hover icon still renders (`verification/CV_LINK_hover_proof.png`); zero external requests, zero failed requests.
- **Visual:** side-by-side screenshots at desktop 1440px and mobile 390px match (see `verification/side_by_side_desktop.png`, `side_by_side_mobile.png`).
- **Confirmed working in the clone:**
  - Framer hydration + appear/scroll animations, hero marquee ticker, rotating role text (5 titles), hover states
  - Sticky pill nav with scroll-spy active highlighting + smooth anchor scrolling
  - **Spline 3D robot rendering fully locally** (`verification/clone_spline_loaded.png`)
  - Mobile hamburger menu overlay (verification/clone_mobile_menu.png)
  - Web fonts (Public Sans, PT Mono, custom Framer fonts), icon modules (ArrowDown, Phone, ReadCvLogo, ArrowUpward)
  - All breakpoints (Framer breakpoint CSS is inline and untouched)
- Meta/SEO tags preserved exactly: title, description, canonical, Open Graph, Twitter card, favicons (light/dark), `framer-search-index` (pointed at the local JSON).

## 5. What is NOT 100% replicated / needs manual attention

| Item | Status | Why / What to do |
|---|---|---|
| Framer analytics (`events.framer.com`) | **Removed intentionally** | Tracking only; re-add the original `<script>` tag if you want view stats. |
| Framer editor bar / "Edit in Framer" | **Replaced with a local no-op stub** (`assets/modules/editorbar-stub.js`) | Editor-only feature tied to the Framer account; irrelevant for a source-code recovery. |
| Backend form submissions | **N/A — none exist on this site.** The contact section only contains external links (cal.com, Instagram, GitHub, Behance). No forms to reconnect. |
| External links | Kept as-is (absolute URLs) | GitHub / Behance / Instagram / cal.com — outbound links, expected to stay absolute. (The floating "Read My CV" pill no longer points to the `original-shares-496620.framer.app` template page — see §3c.) |
| Spline scene internals | Cloned byte-for-byte (4.8 MB embedded scene) | Works locally. If you want to **edit** the 3D scene, re-export it from Spline (the scene belongs to the original Spline account). |
| Icon modules | **Fixed & complete** — 4 wrappers + 4 real icon modules under `assets/modules/` | If you later add icons in Framer, add matching wrapper files under `assets/icons/<phosphor|material-icons>/Name.js` (no `@version` suffix) and the module under `assets/modules/`. |
| Google Fonts / Fontshare loader chunks | Downloaded (metadata only, no remote fetching) | The site's fonts are self-hosted; the loaders resolve locally and never touch the network. |
| Lazy Spline wasm modules (navmesh/boolean/skia-ui) | Downloaded + patched, but unused by this scene | They are the only remaining `unpkg.com` references (dead code paths on the live site too). |
| `framerusercontent.com/third-party-assets/fontshare/` string in a chunk | Left in place | It is an inert URL-prefix classifier (editor feature), never fetched. |
| Canonical URL | Left pointing to `original-shares-496620.framer.app` | That is the site's own SEO canonical, preserved "exactly as found". Change it if you publish the clone under a new domain. |

## 6. Recovered source-code summary

This clone effectively restores your site's deployable source: the SSR HTML (with all inline CSS + breakpoint rules), the full JS bundle (React + Motion + Framer runtime + your site code), all images/illustrations, all fonts, icon components, and the complete self-hosted Spline 3D scene. To edit content you can modify `index.html` text nodes directly, or — recommended — re-import this restored build into Framer using the same account if you still have project access.

**Folder map**

```
amine-portfolio-clone/
├── index.html                  ← the whole site page (SSR HTML, rewritten)
├── assets/
│   ├── images/                 ← 33 images (originals; query-param variants de-duplicated)
│   ├── sites/4WTXJH8SFq8Hw6UXKZPjnX/  ← 14 Framer runtime .mjs chunks + searchIndex JSON
│   ├── modules/                ← icon component modules (framerusercontent modules)
│   ├── icons/                  ← framer.com/m/ wrappers (renamed with @version)
│   └── fonts/                  ← framer/ (37 custom woff2) + gstatic/ (Google woff2)
├── spline/                     ← fully self-hosted Spline 3D scene
│   ├── index.html              ← 4.8 MB scene page (data embedded)
│   └── vendor/                 ← @splinetool runtime + wasm packages (patched to load locally)
├── verification/               ← clone vs live screenshots
├── _extract_manifest.json      ← URL → local path map for every downloaded asset
└── CLONE_REPORT.md             ← this file
```
