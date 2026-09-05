#!/usr/bin/env python3
"""
fix_services_design_3d.py — Patch the Amine portfolio clone so the Services
scroll-story shows exactly 5 design/3D-only slides (no duplicates) AND the
big sticky number + title update together while scrolling.

WHAT THIS SCRIPT DOES
=====================

Working from the original amine-portfolio clone (GitHub: amnabb5/port-101),
this script makes the Services section show exactly these 5 slides — all
design/3D-focused, no web-dev leftovers, no duplicates:

    01  3D Product Ads           (original slide 01)
    02  3D Environment Design    (was "Landing Page Design" — web-related)
    03  Product Visualization    (original slide 03)
    04  Branding & Visual Identity (original slide 06, renumbered)
    05  3D & Motion Design       (original slide 08, renumbered — LAST slide)

After this fix, scrolling through Services shows 5 slides and ends on
"3D & Motion Design" — no duplicates, no leftover slides after it.

CHANGES
=======

1. CSS fix (index.html):
   Replace the broken `<style id="clone-services-five">` block. The previous
   version hid 6 slides then re-showed 4 of them, which leaked 2 duplicate
   slides (Responsive Design + Design Systems) onto the page. The new rule
   hides ONLY the 4 slides that should be hidden:
       .framer-4j0p2h, .framer-1lquz1p, .framer-1f1mc7v, .framer-1q4glo
   (which are slides 04, 05, 07, 09 — Responsive Design, Design Systems,
   Performance Optimization, Maintenance & Support respectively).

2. Slide 02 content replacement (Landing Page Design → 3D Environment Design):
   - SSR <p> description text in index.html
   - Per-section title <h3> in index.html
   - React chunk variant MDqfkQhgK title text
   - React chunk slide-02 description text

3. Slide 08 description wording ("Bring your site to life" → "Bring your ideas to life"):
   - index.html SSR text
   - React chunk text

4. Robust scroll-sync JS injected before </body>:
   Updates BOTH the big 200px number h3 AND its sibling title h3 in the
   sticky Services card based on which visible Description-XX section is
   currently centered. Survives Framer hydration / re-renders by
   re-applying on a timer until the DOM is stable.

The patch is IDEMPOTENT — re-running on an already-patched file is a no-op.

USAGE
=====

    git clone https://github.com/amnabb5/port-101.git
    cd port-101
    python3 fix_services_design_3d.py
    git add -A
    git commit -m "Services: 5 design/3D slides + sticky title scrolls with number"
    git push origin main
"""

from pathlib import Path
import sys
import re

# Resolve paths relative to the CURRENT WORKING DIRECTORY (where the user
# runs the script from — typically the cloned repo root per Option C).
# Falls back to the script's own directory if index.html isn't in CWD.
def _find_repo_root() -> Path:
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent,
    ]
    for c in candidates:
        if (c / "index.html").exists():
            return c
    return Path.cwd()

ROOT = _find_repo_root()
INDEX = ROOT / "index.html"
CHUNK = ROOT / "assets" / "sites" / "4WTXJH8SFq8Hw6UXKZPjnX" / "bQpuC35cZzF-T5TbiIT4UApU9FHXpnYoZdtcdyzTx_8.DN4wskZc.mjs"


# ---------------------------------------------------------------------------
# 1. New CSS rule that PROPERLY hides slides 04, 05, 07, 09 AND forces
#    slides 06, 08 visible (overriding the inline display:none set by the
#    existing serviceContentTimer JS).
#    Old (broken) rule hid 6 classes then re-showed 4 of them — that left
#    slides 04 (Responsive Design) and 05 (Design Systems & UI Kits)
#    visible on the page, creating duplicate Branding + 3D & Motion slides
#    after the real slide 05.
# ---------------------------------------------------------------------------
OLD_CSS_BLOCK = (
    '<style id="clone-services-five">'
    '.framer-4j0p2h,.framer-1lquz1p,.framer-1j3sc5x,.framer-1f1mc7v,.framer-al4pnj,.framer-1q4glo{display:none!important}'
    '.framer-4j0p2h,.framer-1lquz1p{display:flex!important}'
    '.framer-1j3sc5x,.framer-al4pnj{display:flex!important}'
    '</style>'
)
NEW_CSS_BLOCK = (
    '<style id="clone-services-five">'
    # Hide ONLY the 4 slides that should not appear: 04 (Responsive Design),
    # 05 (Design Systems & UI Kits), 07 (Performance Optimization),
    # 09 (Maintenance & Support).
    '.framer-4j0p2h,.framer-1lquz1p,.framer-1f1mc7v,.framer-1q4glo{display:none!important}'
    # Force slides 06 (Branding) and 08 (3D & Motion) visible — the existing
    # serviceContentTimer JS sets inline display:none on them (to "consolidate"
    # their content into slides 04/05), but we want them as the real visible
    # slides 04 and 05 in the user-facing numbering.
    '.framer-1j3sc5x,.framer-al4pnj{display:flex!important}'
    '</style>'
)

# ---------------------------------------------------------------------------
# 2. New slide 02 content (replaces the web-related "Landing Page Design").
# ---------------------------------------------------------------------------
NEW_SLIDE02_TITLE = "3D Environment Design"
NEW_SLIDE02_DESC = (
    "3D Environment DesignWorlds that pull you in. I build fully realized 3D "
    "environments with attention to lighting, atmosphere, and storytelling\u2014"
    "from cinematic set pieces to immersive product worlds. Ideal for film, ads, "
    "games, and branded experiences that need a sense of place."
)
OLD_SLIDE02_DESC = (
    "Landing Page CreationLaser-focused and built to convert. I design sleek, "
    "conversion-optimized landing pages that captivate, inform, and drive "
    "action\u2014perfect for product launches, campaigns, or lead generation. "
    "From scroll-stopping visuals to CTA strategy, every element is crafted "
    "with intent."
)
OLD_SLIDE02_TITLE = "Landing Page Design"

# ---------------------------------------------------------------------------
# 3. Slide 08 description reword (drop "your site" wording).
# ---------------------------------------------------------------------------
OLD_SLIDE08_DESC_SNIPPET = "3D &amp; Motion DesignBring your site to life."
NEW_SLIDE08_DESC_SNIPPET = "3D &amp; Motion DesignBring your ideas to life."
OLD_SLIDE08_DESC_SNIPPET_JS = "3D & Motion DesignBring your site to life."
NEW_SLIDE08_DESC_SNIPPET_JS = "3D & Motion DesignBring your ideas to life."

# ---------------------------------------------------------------------------
# 4. The robust scroll-sync script injected into index.html.
#    Updates both the big 200px number h3 AND the sibling title h3 in the
#    sticky Services card based on which VISIBLE Description-XX section is
#    currently centered.
# ---------------------------------------------------------------------------
SCROLL_SYNC_SCRIPT = """<script id="clone-services-design3d-scrollsync">
// Robust Services scroll-sync: updates both the big number h3 and the
// sibling title h3 in the sticky Services card based on which VISIBLE
// Description-XX section is currently centered. Survives Framer
// hydration / re-renders by re-applying on a timer until the DOM is stable.
window.addEventListener('load', function () {
  var TITLES = [
    '3D Product Ads',
    '3D Environment Design',
    'Product Visualization',
    'Branding & Visual Identity',
    '3D & Motion Design'
  ];

  function findStickyCard() {
    // The sticky card's big number h3 is the FIRST h3 in document order
    // whose trimmed text matches /^0[1-9]$/.
    var h3s = document.querySelectorAll('h3');
    for (var i = 0; i < h3s.length; i++) {
      var t = (h3s[i].textContent || '').trim();
      if (/^0[1-9]$/.test(t)) {
        var big = h3s[i];
        // The title h3 is the next h3 inside the same .framer-g5aayk block.
        var block = big.closest('.framer-g5aayk');
        var titleEl = null;
        if (block) {
          var blockH3s = block.querySelectorAll('h3');
          for (var j = 0; j < blockH3s.length; j++) {
            if (blockH3s[j] !== big && !/^0[1-9]$/.test((blockH3s[j].textContent || '').trim())) {
              titleEl = blockH3s[j];
              break;
            }
          }
        }
        return { big: big, title: titleEl };
      }
    }
    return null;
  }

  function findVisibleScrollSections() {
    // Collect all services-scroll-section-* divs that are actually visible
    // (height > 0). With the CSS fix, only 5 will be visible: 01, 02, 03,
    // 06, 08 — which is what we want.
    var all = document.querySelectorAll('[id^="services-scroll-section-"]');
    var out = [];
    for (var i = 0; i < all.length; i++) {
      var r = all[i].getBoundingClientRect();
      if (r.height > 0 && r.width > 0) out.push(all[i]);
    }
    return out;
  }

  var state = { sections: [], card: null, lastActive: -1 };

  function computeActive() {
    var sections = state.sections;
    if (!sections.length) return 0;
    var center = window.innerHeight / 2;
    var bestIdx = 0;
    var bestDist = Infinity;
    for (var i = 0; i < sections.length; i++) {
      var rect = sections[i].getBoundingClientRect();
      var mid = rect.top + rect.height / 2;
      var dist = Math.abs(mid - center);
      if (dist < bestDist) { bestDist = dist; bestIdx = i; }
    }
    return bestIdx;
  }

  function apply() {
    if (!state.card || state.sections.length < 5) return;
    var active = computeActive();
    if (active === state.lastActive) return;
    state.lastActive = active;
    var numText = '0' + (active + 1);
    if (state.card.big && state.card.big.textContent.trim() !== numText) {
      state.card.big.textContent = numText;
    }
    if (state.card.title && state.card.title.textContent.trim() !== TITLES[active]) {
      state.card.title.textContent = TITLES[active];
    }
  }

  function rebindAndApply() {
    var fresh = findStickyCard();
    if (fresh && (!state.card || state.card.big !== fresh.big || state.card.title !== fresh.title)) {
      state.card = fresh;
      state.lastActive = -1;
    }
    state.sections = findVisibleScrollSections();
    apply();
  }

  // Initial bind: retry every 200ms for up to 10s (covers hydration).
  var tries = 0;
  var bindTimer = setInterval(function () {
    rebindAndApply();
    tries++;
    if (tries > 50) clearInterval(bindTimer);
  }, 200);

  // Long-term watcher: keeps the title in sync even after late hydration /
  // variant swaps. Throttled to every 400ms; cheap (just a text compare).
  var longTimer = setInterval(function () {
    rebindAndApply();
  }, 400);

  // Scroll + resize listeners (real-time updates).
  window.addEventListener('scroll', apply, { passive: true });
  window.addEventListener('resize', apply);
});
</script>"""


def patch_index(path: Path) -> None:
    """Apply all index.html edits in place."""
    html = path.read_text(encoding="utf-8")
    orig = html

    # 1. Fix the CSS block
    if OLD_CSS_BLOCK in html:
        html = html.replace(OLD_CSS_BLOCK, NEW_CSS_BLOCK, 1)
        print("  [1] Fixed <style id='clone-services-five'> CSS — now hides ONLY slides 04/05/07/09")
    elif NEW_CSS_BLOCK in html:
        print("  [1] (already applied) CSS fix")
    else:
        # Maybe a slightly different format — try a regex
        pat = re.compile(r'<style id="clone-services-five">[^<]*</style>', re.IGNORECASE)
        if pat.search(html):
            html = pat.sub(NEW_CSS_BLOCK, html, count=1)
            print("  [1] Replaced existing <style id='clone-services-five'> (regex match)")
        else:
            print("  [1] WARNING: CSS block not found — services section may show duplicate slides")

    # 2. Slide 02 description <p>
    if OLD_SLIDE02_DESC in html:
        html = html.replace(OLD_SLIDE02_DESC, NEW_SLIDE02_DESC, 1)
        print("  [2] Replaced slide 02 description <p>")
    elif NEW_SLIDE02_DESC in html:
        print("  [2] (already applied) slide 02 description")
    else:
        print("  [2] WARNING: slide 02 description not found")

    # 3. Slide 02 per-section title <h3>
    if OLD_SLIDE02_TITLE in html:
        html = html.replace(OLD_SLIDE02_TITLE, NEW_SLIDE02_TITLE)
        print(f"  [3] Replaced slide 02 per-section title -> '{NEW_SLIDE02_TITLE}'")
    else:
        print(f"  [3] (already applied or not found) slide 02 title")

    # 4. Slide 08 description wording ("site" → "ideas")
    if OLD_SLIDE08_DESC_SNIPPET in html:
        html = html.replace(OLD_SLIDE08_DESC_SNIPPET, NEW_SLIDE08_DESC_SNIPPET)
        print("  [4] Replaced slide 08 'site' -> 'ideas'")
    elif NEW_SLIDE08_DESC_SNIPPET in html:
        print("  [4] (already applied) slide 08 wording")
    else:
        print("  [4] WARNING: slide 08 snippet not found")

    # 5. Inject the robust scroll-sync script (idempotent).
    SCRIPT_ID = "clone-services-design3d-scrollsync"
    pat_old_script = re.compile(
        r'<script id="' + SCRIPT_ID + r'">[\s\S]*?</script>',
        re.IGNORECASE
    )
    if pat_old_script.search(html):
        print("  [5] (already applied) robust scroll-sync script")
    elif "</body>" in html:
        html = html.replace("</body>", SCROLL_SYNC_SCRIPT + "\n</body>", 1)
        print("  [5] Injected robust scroll-sync script before </body>")
    else:
        print("  [5] WARNING: no </body> tag found, script not injected")

    # 6. Neutralize the EXISTING scroll-number scripts that look for sections
    #    01-05 (which include hidden slides 04 and 05). These scripts compute
    #    the wrong active section because hidden sections have height=0 and
    #    getBoundingClientRect().top=0, confusing the distance calculation.
    #    We change their section arrays from ['01','02','03','04','05'] to
    #    ['01','02','03','06','08'] (the 5 actually-visible sections).
    OLD_SECTION_ARRAY = "['01', '02', '03', '04', '05']"
    NEW_SECTION_ARRAY = "['01', '02', '03', '06', '08']"
    if OLD_SECTION_ARRAY in html:
        html = html.replace(OLD_SECTION_ARRAY, NEW_SECTION_ARRAY)
        print("  [6a] Updated scroll-number section array -> ['01','02','03','06','08']")
    elif NEW_SECTION_ARRAY in html:
        print("  [6a] (already applied) scroll-number section array")
    else:
        print("  [6a] (not found) scroll-number section array — may use a different format")

    # Also neutralize the second scroll-number script (the setTimeout at the
    # bottom that uses querySelectorAll + slice(0, 5)). Change slice(0, 5) to
    # a filter that only keeps visible sections. We do this by replacing the
    # slice call with a filter for height > 0.
    OLD_SLICE_CALL = (
        "var sections = Array.prototype.slice.call("
        "document.querySelectorAll('[data-framer-name^=\"Services-Scroll-Section-\"]')"
        ").slice(0, 5);"
    )
    NEW_SLICE_CALL = (
        "var sections = Array.prototype.slice.call("
        "document.querySelectorAll('[data-framer-name^=\"Services-Scroll-Section-\"]'"
        ")).filter(function(s){var r=s.getBoundingClientRect();"
        "return r.height>0&&r.width>0;});"
    )
    if OLD_SLICE_CALL in html:
        html = html.replace(OLD_SLICE_CALL, NEW_SLICE_CALL)
        print("  [6b] Updated bottom scroll-number script to filter by visibility")
    elif NEW_SLICE_CALL in html:
        print("  [6b] (already applied) bottom scroll-number script")
    else:
        print("  [6b] (not found) bottom scroll-number script — may use a different format")

    if html != orig:
        path.write_text(html, encoding="utf-8")
        print(f"  Wrote: {path}")
    else:
        print(f"  No changes to write: {path}")


def patch_chunk(path: Path) -> None:
    """Apply React chunk edits in place."""
    if not path.exists():
        print(f"  ERROR: chunk not found at {path}")
        return

    js = path.read_text(encoding="utf-8")
    orig = js
    changes = 0

    # 1. Variant MDqfkQhgK title: "Landing Page Design" → "3D Environment Design"
    pat_slide02_title = re.compile(
        r'(MDqfkQhgK:[\s\S]{0,1500}?children:`)' + re.escape(OLD_SLIDE02_TITLE) + r'(`)',
        re.DOTALL
    )
    if pat_slide02_title.search(js):
        js = pat_slide02_title.sub(r'\g<1>' + NEW_SLIDE02_TITLE + r'\g<2>', js, count=1)
        print(f"  [J1] Replaced variant MDqfkQhgK title -> '{NEW_SLIDE02_TITLE}'")
        changes += 1
    else:
        # The regex didn't match. Check if the new title is already present
        # anywhere in the chunk (the variant ID and its title text can be
        # ~9000 chars apart in the minified chunk).
        if "`" + NEW_SLIDE02_TITLE + "`" in js:
            print(f"  [J1] (already applied) variant MDqfkQhgK title")
        elif "`" + OLD_SLIDE02_TITLE + "`" in js:
            print(f"  [J1] WARNING: old title still in chunk but regex didn't match — manual check needed")
        else:
            print(f"  [J1] WARNING: neither old nor new title found in chunk")

    # 2. Slide 02 description text in the chunk
    if OLD_SLIDE02_DESC in js:
        js = js.replace(OLD_SLIDE02_DESC, NEW_SLIDE02_DESC, 1)
        print(f"  [J2] Replaced slide 02 description in chunk")
        changes += 1
    elif NEW_SLIDE02_DESC in js:
        print(f"  [J2] (already applied) slide 02 description in chunk")
    else:
        print(f"  [J2] WARNING: slide 02 description not found in chunk")

    # 3. Slide 08 description snippet in the chunk (no &amp; here — raw text)
    if OLD_SLIDE08_DESC_SNIPPET_JS in js:
        js = js.replace(OLD_SLIDE08_DESC_SNIPPET_JS, NEW_SLIDE08_DESC_SNIPPET_JS)
        print(f"  [J3] Replaced slide 08 'site' -> 'ideas' in chunk")
        changes += 1
    elif NEW_SLIDE08_DESC_SNIPPET_JS in js:
        print(f"  [J3] (already applied) slide 08 wording in chunk")
    else:
        print(f"  [J3] WARNING: slide 08 snippet not found in chunk")

    if js != orig:
        path.write_text(js, encoding="utf-8")
        print(f"  Wrote: {path} ({changes} change(s))")
    else:
        print(f"  No changes to write: {path}")


def main() -> int:
    if not INDEX.exists():
        print(f"ERROR: index.html not found at {INDEX}", file=sys.stderr)
        print("Run this script from inside the cloned port-101 repo root:", file=sys.stderr)
        print("  git clone https://github.com/amnabb5/port-101.git", file=sys.stderr)
        print("  cd port-101", file=sys.stderr)
        print("  python3 fix_services_design_3d.py", file=sys.stderr)
        return 1

    print("=" * 70)
    print("Patching index.html (SSR HTML)")
    print("=" * 70)
    patch_index(INDEX)

    print()
    print("=" * 70)
    print("Patching React chunk (bQpuC35cZzF-*.mjs)")
    print("=" * 70)
    patch_chunk(CHUNK)

    print()
    print("=" * 70)
    print("Done. Summary of what changed:")
    print("=" * 70)
    print("""
Services section now shows exactly 5 design/3D slides (no duplicates):

    01  3D Product Ads           (original slide 01)
    02  3D Environment Design    (was "Landing Page Design" — web-related)
    03  Product Visualization    (original slide 03)
    04  Branding & Visual Identity (original slide 06, renumbered)
    05  3D & Motion Design       (original slide 08, renumbered — LAST slide)

Slides 04, 05, 07, 09 (Responsive Design, Design Systems, Performance,
Maintenance) are now properly hidden via CSS — no duplicates leak through.

The sticky 200px number h3 + sibling title h3 swap together on scroll,
matching the original amine-portfolio-3d.onrender.com behavior.

To verify:
    python3 -m http.server 8080
    open http://localhost:8080/  -> scroll through the Services section
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
