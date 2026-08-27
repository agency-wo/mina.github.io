#!/usr/bin/env python3
# [ERR-003] test_sync_stock.py — pins the rebuild leg's flip semantics and the
# byte formats that keep a no-op run at zero diff. Stdlib only; no network.
# Run: python tools/test_sync_stock.py   (the Action and the tracker's battery
# both run it 3×; a format drift here means phantom commits every night).
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_stock import apply_stock, json_bytes, data_js_bytes, style_of  # noqa: E402

BASE = Path(__file__).resolve().parent.parent


def w(i, ref, sold=False):
    return {"id": i, "reference": ref, "sold": sold}


class ApplyStock(unittest.TestCase):
    def test_sold_out_flips_to_sold(self):
        ws = [w("a", "X-1")]
        changed, rep = apply_stock(ws, {"X-1": 0})
        self.assertEqual(changed, ["a"])
        self.assertTrue(ws[0]["sold"])

    def test_restock_flips_back(self):
        ws = [w("a", "X-1", sold=True)]
        changed, _ = apply_stock(ws, {"X-1": 2})
        self.assertEqual(changed, ["a"])
        self.assertFalse(ws[0]["sold"])

    def test_unlinked_untouched(self):
        ws = [w("a", "NOT-IN-CRM"), w("b", "")]
        changed, rep = apply_stock(ws, {"X-1": 0})
        self.assertEqual(changed, [])
        self.assertEqual(sorted(rep["unlinked"]), ["a", "b"])
        self.assertFalse(ws[0].get("sold"))

    def test_duplicate_refs_reported_never_guessed(self):
        ws = [w("a", "D-1"), w("b", "d-1 ")]      # same ref after normalization
        changed, rep = apply_stock(ws, {"D-1": 0})
        self.assertEqual(changed, [])
        self.assertIn("D-1", rep["dups"])
        self.assertFalse(ws[0].get("sold"))

    def test_normalization_matches_the_feed(self):
        ws = [w("a", " nm-12 ")]
        changed, _ = apply_stock(ws, {"NM-12": 0})
        self.assertEqual(changed, ["a"])

    def test_idempotent_replay(self):
        ws = [w("a", "X-1"), w("b", "Y-2", sold=True)]
        stock = {"X-1": 0, "Y-2": 0}
        first, _ = apply_stock(ws, stock)
        second, _ = apply_stock(ws, stock)
        self.assertEqual(first, ["a"])
        self.assertEqual(second, [])

    def test_empty_feed_changes_nothing(self):
        ws = [w("a", "X-1", sold=True)]
        changed, _ = apply_stock(ws, {})
        self.assertEqual(changed, [])
        self.assertTrue(ws[0]["sold"])

    def test_deleted_entries_are_nobodys_to_flip(self):
        ws = [dict(w("a", "X-1"), deleted=True)]
        changed, rep = apply_stock(ws, {"X-1": 0})
        self.assertEqual(changed, [])
        self.assertFalse(ws[0].get("sold"))
        self.assertNotIn("a", rep["unlinked"])   # not owner-actionable either


class NeverConflicts(unittest.TestCase):
    """The guarantees the owner asked for: the CRM and the site cannot corrupt
    each other, whichever side an edit happens on.

    The two stores deliberately hold different sets. The CRM has watches the
    site has never published (46 of 56 references, measured 2026-08-27) and the
    site has watches the CRM has never seen (59 of 69). Only 10 are linked.
    Every test here is a property of that overlap, not of today's catalogue.
    """

    def test_crm_only_watch_selling_touches_nothing(self):
        """A watch in the CRM but not on the site is inert, in every state.

        apply_stock iterates SITE entries, so a CRM key nothing references is
        never read. This is the owner's stated worry and the answer is
        structural rather than a check that could be removed."""
        ws = [w("site", "AAA")]
        before = json.dumps(ws, sort_keys=True)
        changed, _ = apply_stock(ws, {"AAA": 1, "CRM-ONLY-A": 0, "CRM-ONLY-B": 7})
        self.assertEqual(changed, [])
        self.assertEqual(json.dumps(ws, sort_keys=True), before)

    def test_admin_edit_survives_the_nightly_reconcile(self):
        """A watch the CRM has never seen belongs to the admin panel alone.

        59 of 69 records are in this class, so this is the ordinary case rather
        than the edge one: marking one sold in the panel must still be true
        after the 05:17 reconcile runs."""
        ws = [w("no-ref", "", sold=True), w("unknown-ref", "ZZZ", sold=True)]
        changed, rep = apply_stock(ws, {"AAA": 5})
        self.assertEqual(changed, [])
        self.assertTrue(all(x["sold"] for x in ws))
        self.assertEqual(sorted(rep["unlinked"]), ["no-ref", "unknown-ref"])

    def test_archive_outranks_crm_availability(self):
        """Archiving is an editorial decision and the CRM cannot undo it.

        A restock in the CRM must never silently republish a watch the owner
        pulled off the site."""
        ws = [dict(w("arch", "AAA", sold=True), deleted=True)]
        changed, _ = apply_stock(ws, {"AAA": 9})
        self.assertEqual(changed, [])
        self.assertTrue(ws[0]["deleted"])

    def test_archived_ref_does_not_block_the_watch_that_replaces_it(self):
        """The restock path the archive exists for: retire the sold one, put its
        identical twin back on sale.

        A retired record keeps its shifra forever, so both entries carried the
        same reference, the duplicate guard read them as ambiguous and refused
        to link EITHER. The live watch could then never follow the CRM again.
        Silent, and permanent until someone read the linking report."""
        ws = [dict(w("retired", "NM-12", sold=True), deleted=True),
              w("back-in-stock", "NM-12")]
        changed, rep = apply_stock(ws, {"NM-12": 0})
        self.assertEqual(changed, ["back-in-stock"])
        self.assertEqual(rep["dups"], {})
        self.assertTrue(ws[1]["sold"])

    def test_two_live_entries_sharing_a_ref_still_block(self):
        """The fix above must not weaken the real ambiguity beside it."""
        ws = [w("a", "NM-12"), w("b", "NM-12")]
        changed, rep = apply_stock(ws, {"NM-12": 0})
        self.assertEqual(changed, [])
        self.assertIn("NM-12", rep["dups"])
        self.assertFalse(ws[0].get("sold"))


class RebuildSurvives(unittest.TestCase):
    """P128: two ordinary events used to kill the whole rebuild leg for good.

    A brand selling out (Bigotti has four watches) made gen_brand_pages assert,
    and un-retiring a watch fed a redirect stub to the page patcher. Both are
    steps of the stock-sync Action, so one sale froze the site silently."""

    def test_brand_with_no_unsold_watches_is_skipped_not_fatal(self):
        sys.path.insert(0, str(BASE))
        import gen_brand_pages as g
        # the generator must handle an empty brand rather than assert on it
        src = (BASE / "gen_brand_pages.py").read_text(encoding="utf-8")
        self.assertIn("if not brand_watches(brand):", src)
        self.assertIn("continue", src.split("if not brand_watches(brand):")[1][:80])
        # and it must SAY which brands it skipped
        self.assertIn("NOTE: no unsold watches for", src)

    def test_unretired_stub_is_reported_not_crashed(self):
        src = (BASE / "gen_product_pages.py").read_text(encoding="utf-8")
        self.assertIn('if not w.get("deleted") and \'id="watch-content"\' not in html:', src)
        self.assertIn("make-new-watch-pages.py", src)

    def test_sold_page_carries_the_runtime_contract(self):
        """A statically-sold page must be un-flippable by stock-live.js."""
        src = (BASE / "gen_product_pages.py").read_text(encoding="utf-8")
        self.assertIn('stock-oos-badge', src)
        self.assertIn('stock-notify', src)
        self.assertIn('" stock-oos" if sold else ""', src)

    def test_hub_prices_only_what_can_be_bought(self):
        """A sold watch must not set the published price band or the brand count.

        This used to assert through {n}. That token is retired — no page states
        how many watches, because the shop stocks more than it lists — so the
        same property is proved through the bounds, which is where a sold watch
        did real damage: it could advertise a floor whose watch was gone."""
        sys.path.insert(0, str(BASE))
        from shop_seo import fill
        ws = [{"brand": "A", "price": 50}, {"brand": "B", "price": 200, "sold": True}]
        out = fill("from EUR{lo} to EUR{hi}, {b} brands", ws)
        self.assertEqual(out, "from EUR50 to EUR50, 1 brands")

    def test_hub_refuses_to_publish_a_count(self):
        """{n} in copy must fail the build, not render a number that understates."""
        sys.path.insert(0, str(BASE))
        from shop_seo import fill
        with self.assertRaises(AssertionError):
            fill("{n} watches from EUR{lo}", [{"brand": "A", "price": 50}])


class DeletedStub(unittest.TestCase):
    """A retired watch's page becomes the standard noindex redirect stub.

    Imported from shop_bits ON PURPOSE: gen_product_pages runs its page loop
    at module level — importing IT from a test regenerates all 171 pages."""

    def test_stub_shape(self):
        sys.path.insert(0, str(BASE))
        from shop_bits import stub_html
        s = stub_html({"id": "watch-9", "brand": "Navimarine", "model": "NMM1011"}, "sq")
        self.assertIn('name="robots" content="noindex, follow"', s)
        self.assertIn('url=/sq/shop/', s)
        self.assertIn('canonical" href="https://watch.al/sq/shop/"', s)
        self.assertIn('Kjo orë nuk është më në katalog.', s)


class ByteFormats(unittest.TestCase):
    """A no-op reconcile must be byte-identical or every night commits noise.

    EOL/BOM are MIRRORED from the existing files, because git materializes LF
    on the Action's Linux runner and CRLF on the owner's autocrlf Windows
    tree — the same repo, two byte shapes (the first Action run failed here).
    """

    def test_watches_json_roundtrip(self):
        raw = (BASE / "watches.json").read_bytes()
        data = json.loads(raw.decode("utf-8-sig"))
        eol, bom = style_of(raw)
        self.assertEqual(json_bytes(data, eol, bom), raw)

    def test_watches_data_js_roundtrip(self):
        raw = (BASE / "watches-data.js").read_bytes()
        data = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))
        eol, bom = style_of(raw)
        self.assertEqual(data_js_bytes(data, eol, bom), raw)


if __name__ == "__main__":
    unittest.main(verbosity=1)
