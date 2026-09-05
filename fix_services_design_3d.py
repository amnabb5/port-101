#!/usr/bin/env python3
"""
fix_services_design_3d.py — Patch the Amine portfolio clone so the Services
scroll-story shows 5 design/3D-only slides AND the big number + title both
update together while scrolling (matching the original site's behavior).

Changes
-------
A. Slide 02 content replacement (Landing Page Design → 3D Environment Design):
   - SSR <p> description text in index.html
   - per-section title <h3> in index.html (mobile view)
   - React chunk variant MDqfkQhgK title text
   - React chunk slide-02 description text

B. Slide 04 per-section title (mobile view, was "Responsive Design"):
   - index.html per-section <h3> → "Branding & Visual Identity"

C. Slide 05 per-section title (mobile view, was "Design Systems & UI Kits"):
   - index.html per-section <h3> → "3D & Motion Design"

D. Slide 08 description wording:
   - "Bring your site to life" → "Bring your ideas to life"
   - Applied in both index.html (SSR text) and the React chunk

E. Robust scroll-sync JS for the sticky card:
   - Updates BOTH the big 200px number <h3> AND its sibling title <h3>
     based on which Description-XX is currently centered in the viewport.
   - Re-applies periodically so Framer hydration / re-renders cannot revert it.
   - Consolidates (and supersedes) the two earlier scroll listeners that
     only updated the number.

Idempotent: re-running on an already-patched file is a no-op.
"""

from pathlib import Path
import sys
import re

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
CHUNK = ROOT / "assets/sites/4WTXJH8SFq8Hw6UXKZPjnX/bQpuC35cZzF-T5TbiIT4UApU9FHXpnYoZdtcdyzTx_8.DN4wskZc.mjs"

# ---------------------------------------------------------------------------
# New slide 02 content (replaces "Landing Page Creation" — web-related)
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
# Slide 08 description reword (drop "your site" wording)
# ---------------------------------------------------------------------------
OLD_SLIDE08_DESC_SNIPPET = "3D &amp; Motion DesignBring your site to life."
NEW_SLIDE08_DESC_SNIPPET = "3D &amp; Motion DesignBring your ideas to life."
OLD_SLIDE08_DESC_SNIPPET_JS = "3D & Motion DesignBring your site to life."
NEW_SLIDE08_DESC_SNIPPET_JS = "3D & Motion DesignBring your ideas to life."

# ---------------------------------------------------------------------------
# Per-section titles for slides 04 and 05 (mobile view) — fix mismatched
# titles that arose from renumbering slide 06→04 and 08→05.
# ---------------------------------------------------------------------------
OLD_SLIDE04_TITLE = "Responsive Design"
NEW_SLIDE04_TITLE = "Branding &amp; Visual Identity"
OLD_SLIDE05_TITLE = "Design Systems &amp; UI Kits"
NEW_SLIDE05_TITLE = "3D &amp; Motion Design"

# ---------------------------------------------------------------------------
# The robust scroll-sync script that we inject into index.html.
# Updates both the big 200px number h3 AND the sibling title h3 in the sticky
# Services card so both change in lockstep with the active Description-XX.
# ---------------------------------------------------------------------------
SCROLL_SYNC_SCRIPT = """<script id="clone-services-design3d-scrollsync">
// Robust Services scroll-sync: updates both the big number h3 and the
// sibling title h3 in the sticky Services card based on which Description-XX
// section is currently centered. Survives Framer hydration / re-renders
// by re-applying on a timer until the DOM is stable.
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
    // whose trimmed text matches /^0[1-5]$/.
    var h3s = document.querySelectorAll('h3');
    for (var i = 0; i < h3s.length; i++) {
      var t = (h3s[i].textContent || '').trim();
      if (/^0[1-5]$/.test(t)) {
        var big = h3s[i];
        // The title h3 is the next h3 inside the same .framer-g5aayk block.
        var block = big.closest('.framer-g5aayk');
        var titleEl = null;
        if (block) {
          var blockH3s = block.querySelectorAll('h3');
          // First h3 is the big number; second is the title.
          for (var j = 0; j < blockH3s.length; j++) {
            if (blockH3s[j] !== big && !/^0[1-5]$/.test((blockH3s[j].textContent || '').trim())) {
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

  function findScrollSections() {
    var ids = ['01', '02', '03', '04', '05'];
    var out = [];
    for (var i = 0; i < ids.length; i++) {
      var el = document.getElementById('services-scroll-section-' + ids[i]);
      if (el) out.push(el);
    }
    return out;
  }

  var state = { sections: [], card: null, lastActive: -1, stableCount: 0 };

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
    if (active === state.lastActive) {
      state.stableCount++;
      return;
    }
    state.lastActive = active;
    var numText = '0' + (active + 1);
    if (state.card.big && state.card.big.textContent.trim() !== numText) {
      state.card.big.textContent = numText;
    }
    if (state.card.title && state.card.title.textContent.trim() !== TITLES[active]) {
      state.card.title.textContent = TITLES[active];
    }
  }

  // Periodically re-resolve the card (Framer may swap its h3 nodes on
  // hydration / variant change). Once the same node has been stable for
  // several ticks, we throttle to scroll/resize only.
  function rebindAndApply() {
    var fresh = findStickyCard();
    if (fresh && (!state.card || state.card.big !== fresh.big || state.card.title !== fresh.title)) {
      state.card = fresh;
      state.lastActive = -1; // force re-apply on next apply()
    }
    state.sections = findScrollSections();
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

    # A. Slide 02 description <p>
    if OLD_SLIDE02_DESC in html:
        html = html.replace(OLD_SLIDE02_DESC, NEW_SLIDE02_DESC, 1)
        print(f"  [A1] Replaced slide 02 description <p> in {path.name}")
    elif NEW_SLIDE02_DESC in html:
        print(f"  [A1] (already applied) slide 02 description in {path.name}")
    else:
        print(f"  [A1] WARNING: slide 02 description not found in {path.name}")

    # B. Slide 02 per-section title <h3>
    if OLD_SLIDE02_TITLE in html:
        html = html.replace(OLD_SLIDE02_TITLE, NEW_SLIDE02_TITLE)
        print(f"  [A2] Replaced slide 02 per-section title -> '{NEW_SLIDE02_TITLE}'")
    else:
        print(f"  [A2] (already applied or not found) slide 02 title")

    # C. Slide 04 per-section title (only the first occurrence after
    #    Description-04 marker — there are multiple "Responsive Design" strings
    #    across the page, so we target the per-section title h3 specifically).
    pat_04 = re.compile(
        r'(data-framer-name="Description-04"[\s\S]{0,4000}?'
        r'<h3 class="framer-text framer-styles-preset-83172e"[^>]*>)'
        + re.escape(OLD_SLIDE04_TITLE)
        + r'(</h3>)',
        re.DOTALL
    )
    if pat_04.search(html):
        html = pat_04.sub(r'\g<1>' + NEW_SLIDE04_TITLE + r'\g<2>', html, count=1)
        print(f"  [B] Replaced slide 04 per-section title -> 'Branding & Visual Identity'")
    elif "Branding &amp; Visual Identity</h3>" in html and "Responsive Design" in html:
        # Already patched (Branding string present) but Responsive Design still
        # elsewhere (probably in another section's <p>) — that's fine.
        print(f"  [B] (already applied) slide 04 title")
    else:
        print(f"  [B] WARNING: slide 04 title not found")

    # D. Slide 05 per-section title — same approach.
    pat_05 = re.compile(
        r'(data-framer-name="Description-05"[\s\S]{0,4000}?'
        r'<h3 class="framer-text framer-styles-preset-83172e"[^>]*>)'
        + re.escape(OLD_SLIDE05_TITLE)
        + r'(</h3>)',
        re.DOTALL
    )
    if pat_05.search(html):
        html = pat_05.sub(r'\g<1>' + NEW_SLIDE05_TITLE + r'\g<2>', html, count=1)
        print(f"  [C] Replaced slide 05 per-section title -> '3D & Motion Design'")
    else:
        print(f"  [C] (already applied or not found) slide 05 title")

    # E. Slide 08 description snippet ("Bring your site to life" → "Bring your ideas to life")
    if OLD_SLIDE08_DESC_SNIPPET in html:
        html = html.replace(OLD_SLIDE08_DESC_SNIPPET, NEW_SLIDE08_DESC_SNIPPET)
        print(f"  [D] Replaced slide 08 'site' → 'ideas' in {path.name}")
    elif NEW_SLIDE08_DESC_SNIPPET in html:
        print(f"  [D] (already applied) slide 08 wording")
    else:
        print(f"  [D] WARNING: slide 08 snippet not found")

    # F. Inject the robust scroll-sync script (idempotent: remove any prior copy first).
    SCRIPT_ID = "clone-services-design3d-scrollsync"
    pat_old_script = re.compile(
        r'<script id="' + SCRIPT_ID + r'">[\s\S]*?</script>',
        re.IGNORECASE
    )
    if pat_old_script.search(html):
        html = pat_old_script.sub("", html)
        print(f"  [E1] Removed previous scroll-sync script")
    # Inject just before </body>
    if "</body>" in html:
        html = html.replace("</body>", SCROLL_SYNC_SCRIPT + "\n</body>", 1)
        print(f"  [E2] Injected robust scroll-sync script before </body>")
    else:
        print(f"  [E2] WARNING: no </body> tag found, script not injected")

    if html != orig:
        path.write_text(html, encoding="utf-8")
        print(f"  Wrote: {path}")
    else:
        print(f"  No changes to write: {path}")


def patch_chunk(path: Path) -> None:
    """Apply React chunk edits in place."""
    js = path.read_text(encoding="utf-8")
    orig = js
    changes = 0

    # 1. Variant MDqfkQhgK title: "Landing Page Design" → "3D Environment Design"
    #    The variant title is rendered as: children:`Landing Page Design`
    #    Look for the variant override context: MDqfkQhgK:{...children:`Landing Page Design`
    pat_slide02_title = re.compile(
        r'(MDqfkQhgK:[\s\S]{0,1500}?children:`)' + re.escape(OLD_SLIDE02_TITLE) + r'(`)',
        re.DOTALL
    )
    m = pat_slide02_title.search(js)
    if m:
        js = pat_slide02_title.sub(r'\g<1>' + NEW_SLIDE02_TITLE + r'\g<2>', js, count=1)
        print(f"  [J1] Replaced variant MDqfkQhgK title -> '{NEW_SLIDE02_TITLE}'")
        changes += 1
    else:
        # Maybe already patched, or different surrounding context.
        # Try a simpler search: just the children:`...` near MDqfkQhgK
        idx = js.find("MDqfkQhgK")
        if idx >= 0:
            window = js[idx:idx+3000]
            if "`" + OLD_SLIDE02_TITLE + "`" in window:
                # Use a more targeted regex
                pat_simple = re.compile(r'children:`' + re.escape(OLD_SLIDE02_TITLE) + r'`')
                js = pat_simple.sub('children:`' + NEW_SLIDE02_TITLE + '`', js, count=1)
                print(f"  [J1] Replaced variant MDqfkQhgK title (simple match) -> '{NEW_SLIDE02_TITLE}'")
                changes += 1
            elif "`" + NEW_SLIDE02_TITLE + "`" in window:
                print(f"  [J1] (already applied) variant MDqfkQhgK title")
            else:
                print(f"  [J1] WARNING: variant MDqfkQhgK title context not found")
        else:
            print(f"  [J1] WARNING: variant MDqfkQhgK not found in chunk")

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
        print(f"  [J3] Replaced slide 08 'site' → 'ideas' in chunk")
        changes += 1
    elif NEW_SLIDE08_DESC_SNIPPET_JS in js:
        print(f"  [J3] (already applied) slide 08 wording in chunk")
    else:
        print(f"  [J3] WARNING: slide 08 snippet not found in chunk")

    # 4. Per-section title h3 for slides 04 and 05 in the chunk's variant map.
    #    On mobile, each Description-XX renders its own number+title block via
    #    Framer hydration. The variant IDs are:
    #      NVW1Z7b4f (Desktop-04) — currently "Responsive Design"  → "Branding & Visual Identity"
    #      GMNOkfc3V (Desktop-05) — currently "Design Systems & UI Kits" → "3D & Motion Design"
    #    We only swap the FIRST occurrence of each (the title h3 inside the
    #    variant definition), NOT the description <p> (which already starts
    #    with the same string — that one is overwritten client-side by the
    #    existing serviceContentTimer JS).
    OLD_SLIDE04_TITLE_JS = "Responsive Design"
    NEW_SLIDE04_TITLE_JS = "Branding & Visual Identity"
    OLD_SLIDE05_TITLE_JS = "Design Systems & UI Kits"
    NEW_SLIDE05_TITLE_JS = "3D & Motion Design"

    # The title h3 in the variant def is: children:`<title>`
    # Pattern is unique because of the surrounding context:
    #   NVW1Z7b4f:{children:m(s,{children:m(T.h3,{...children:`Responsive Design`})})}
    # We match the variant block start, then up to 2000 chars of body, then
    # the children:`...` we want to replace.
    pat_slide04_title_js = re.compile(
        r'(NVW1Z7b4f:[\s\S]{0,2000}?children:`)' + re.escape(OLD_SLIDE04_TITLE_JS) + r'(`)',
        re.DOTALL
    )
    if pat_slide04_title_js.search(js):
        js = pat_slide04_title_js.sub(r'\g<1>' + NEW_SLIDE04_TITLE_JS + r'\g<2>', js, count=1)
        print(f"  [J4] Replaced variant NVW1Z7b4f per-section title -> 'Branding & Visual Identity'")
        changes += 1
    else:
        # Already patched?
        # Search for NVW1Z7b4f with new title
        idx = js.find('NVW1Z7b4f')
        if idx >= 0:
            window = js[idx:idx+2500]
            if '`' + NEW_SLIDE04_TITLE_JS + '`' in window:
                print(f"  [J4] (already applied) variant NVW1Z7b4f title")
            else:
                print(f"  [J4] WARNING: variant NVW1Z7b4f title context not matched")

    pat_slide05_title_js = re.compile(
        r'(GMNOkfc3V:[\s\S]{0,2000}?children:`)' + re.escape(OLD_SLIDE05_TITLE_JS) + r'(`)',
        re.DOTALL
    )
    if pat_slide05_title_js.search(js):
        js = pat_slide05_title_js.sub(r'\g<1>' + NEW_SLIDE05_TITLE_JS + r'\g<2>', js, count=1)
        print(f"  [J5] Replaced variant GMNOkfc3V per-section title -> '3D & Motion Design'")
        changes += 1
    else:
        idx = js.find('GMNOkfc3V')
        if idx >= 0:
            window = js[idx:idx+2500]
            if '`' + NEW_SLIDE05_TITLE_JS + '`' in window:
                print(f"  [J5] (already applied) variant GMNOkfc3V title")
            else:
                print(f"  [J5] WARNING: variant GMNOkfc3V title context not matched")

    if js != orig:
        path.write_text(js, encoding="utf-8")
        print(f"  Wrote: {path} ({changes} change(s))")
    else:
        print(f"  No changes to write: {path}")


def main() -> int:
    if not INDEX.exists():
        print(f"ERROR: index.html not found at {INDEX}", file=sys.stderr)
        return 1
    if not CHUNK.exists():
        print(f"ERROR: chunk not found at {CHUNK}", file=sys.stderr)
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
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
