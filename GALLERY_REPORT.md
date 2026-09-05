# Media Gallery Report — Google Drive → Projects Tab

Source: `https://drive.google.com/drive/folders/1sfaNY-nfHA6Ol5-pWCHXdJ_opH8OeIxf`
Integrated: self-hosted gallery inside the existing **Projects** section of the portfolio clone.

---

## 1. How the content was organized (and why)

The Drive folder had a clean subfolder structure, so it was used **directly as the gallery's category system** — no invented taxonomy:

| Drive subfolder | Gallery category | Items |
|---|---|---|
| `animation` | Animation | 1 |
| `cgi` | CGI | 1 |
| `environment` | Environment | 9 |
| `products-ads` | Products Ads | 5 |

These four categories also mirror the site's own Services positioning (3D Product Ads, Product Visualization, 3D & Motion Design), so the filter tabs read like the rest of the site. "All" is the default tab (16 tiles). Every tile carries a small category chip, and videos additionally show a duration chip + center play button.

Item titles are humanized filenames (e.g. `mercedes one.mov` → "Mercedes One", `Untitled video - Made with Clipchamp (1).mp4` → "Untitled Video"). Nothing was renamed in Drive; only the display copy was cleaned.

## 2. Import results — every file accounted for

All **16 files** downloaded and appear in the gallery: 12 videos + 4 photos. **Zero failures.** Two exact duplicates were detected by checksum and are stored once but listed twice (faithful to Drive, which holds them in two folders each):

| File A | File B (identical content) |
|---|---|
| `cgi/Post insta.mp4` (110.3 MB) | `environment/Copy of Post insta.mp4` |
| `products-ads/Image0001.png` (3.0 MB) | `environment/Copy of Image0001.png` |

**Files that may need manual attention (imported fine, but naming/content is generic):**
- `environment/Untitled video - Made with Clipchamp (1).mp4` — titled "Untitled Video"; rename in Drive and re-run `scripts/build_gallery_js.py` if you want a real name.
- `environment/0001-0196.mp4`, `final0001-0953.mov`, `final30001-0291.mov` — render-sequence names, titled as-is ("Frames 0001-0196", "Final 0001-0953", …).
- Videos keep their original audio (AAC 96 kbps).

## 3. Media optimization — 530 MB → 41 MB

| Step | Detail |
|---|---|
| Videos (12) | Transcoded to H.264 MP4, long edge 1280 px, max 30 fps, CRF 26, `+faststart` (streams immediately), audio AAC 96 kbps. `.mov` sources (which browsers may not play) are now standard `.mp4`. |
| Video posters | WebP stills grabbed at ~25% of each clip (avoids black first frames), 800 px, shown in the grid — **full video loads only when clicked**. |
| Photos (4) | WebP q82 at 1600 px for the lightbox + 800 px q72 thumbs for the grid. |

Posters/thumbs are lazy-loaded (`loading=lazy` + fade-in on load); each tile has a fixed `aspect-ratio` box with a shimmer placeholder, so nothing shifts while loading and nothing "looks broken".

## 4. Design decisions (where the site gave no explicit guidance)

The design system was audited first and reused, not reinvented: Public Sans (headings), PT Mono (kicker/labels/counters, same as the "CLICK HER" display text), Inter (captions), orange `#f94706` as the single accent (same token as the nav "Selected" pill), `#f2f2f2` surfaces, 24 px card radius, 48 px lightbox-media radius, `0 5px 20px rgba(0,0,0,.05)` shadows, backdrop-blur (10 px) lightbox overlay, and the site's 1200 px content grid. Choices made where the template was silent:

1. **Placement:** inside the Projects section, directly after the "CLICK HER" Behance placeholder and before the footer CTA — reached via the existing **Projects** nav tab (no nav changes). The section's own "Projects" heading already names the tab, so the gallery got a secondary heading ("Gallery & Reels") plus a PT Mono kicker ("SELECTED WORK ///") instead of repeating "Projects".
2. **Grid:** uniform 4-per-row card grid (auto-fill, min 280 px; 2-per-row tablet, 1-per-row phones) with `object-fit: cover` rather than a masonry of mixed ratios — the source media is mostly 16:9 reels, and uniform cards match the site's card-like pill/circle language. The Projects content column is ~600 px wide, so the gallery breaks out to the site's full 1200 px grid while staying centered on the viewport.
3. **Filter pills** copy the nav pill shape (21 px radius, orange active state, black hover).
4. **Video behavior:** posters in the grid; click opens the lightbox which then sets the `<video src>` (autoplay + controls + loop). Closing the lightbox removes the `src` so nothing keeps downloading. Keyboard: ←/→ navigate, Esc closes; side arrows and close button use the site's black/white circle icon language.
5. **Hydration safety:** the whole gallery is vanilla JS/CSS (`.gp-*` namespaced), injected **after** Framer's hydration completes, so React never owns the nodes. Verified by a resize-across-breakpoints test (gallery survives; no hydration errors). CSS/font usage only — zero new external requests.

## 5. Verification (Playwright, Chromium)

- 16/16 tiles render; lazy-load confirmed (16/16 loaded after scrolling into view).
- Filters: "Products Ads" → exactly 5 tiles, correct chips; back to "All" → 16.
- Lightbox: photo opens full-size; video loads **on click** (`mercedes-one.mp4`, metadata + playback confirmed); ←/→ navigation; Esc closes; video `src` released on close.
- Existing site untouched: every non-Projects section sits at the exact pre-gallery offset; nav scroll-spy still highlights "Projects" in orange over the gallery.
- Responsive: 1440 px → 4 columns, 900 px → 2, 390 px → 1; no horizontal overflow; gallery survives breakpoint resizes.
- Network: 0 console errors, 0 failed requests, **0 external requests** (fully offline).
- Screenshots: `verification/gallery_desktop_grid.png`, `gallery_desktop_view.png`, `gallery_lightbox_photo.png`, `gallery_lightbox_video.png`, `gallery_tablet_view.png`, `gallery_mobile_view.png`.

## 6. Where things live

```
assets/gallery/
├── animation/mercedes-one.mp4 + -poster.webp
├── cgi/post-insta.mp4 + -poster.webp
├── environment/… (8 media + posters/thumbs)
├── products-ads/…
├── gallery.css   (all styles, .gp-* namespaced)
└── gallery.js    (manifest embedded — no fetch, works over file:// too)
scripts/          (pipeline, re-runnable: download_drive.py → process_media.py
                   → build_gallery_js.py → wire_gallery.py → verify_gallery.py)
```

`index.html` was touched only in `<head>` (one `<link>` + one deferred `<script>`). Raw Drive sources kept at `staging/drive_raw/` for re-processing.
