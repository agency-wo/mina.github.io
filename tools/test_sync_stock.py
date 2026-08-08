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
