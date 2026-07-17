import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "assets/js/app.js").read_text(encoding="utf-8")


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.images = []
        self.scripts = []
        self.stylesheets = []
        self.exercise_ids = []
        self.h1_count = 0
        self.lang = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang")
        if "id" in values:
            self.ids.append(values["id"])
        if tag == "a" and "href" in values:
            self.links.append(values["href"])
        if tag == "img":
            self.images.append(values)
        if tag == "script" and "src" in values:
            self.scripts.append(values["src"])
        if tag == "link" and values.get("rel") == "stylesheet":
            self.stylesheets.append(values.get("href"))
        if tag == "h1":
            self.h1_count += 1
        if tag == "article" and "exercise-card" in values.get("class", "").split():
            self.exercise_ids.append(values.get("id"))


class WebsiteQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = SiteParser()
        cls.parser.feed(HTML)

    def test_document_structure_is_accessible(self):
        self.assertEqual(self.parser.lang, "en")
        self.assertEqual(self.parser.h1_count, 1)
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)), "duplicate HTML id")
        self.assertIn("main", self.parser.ids)
        for image in self.parser.images:
            self.assertIn("alt", image, f"missing alt text: {image.get('src')}")

    def test_internal_anchors_resolve(self):
        known_ids = set(self.parser.ids)
        for href in self.parser.links:
            if href.startswith("#"):
                self.assertIn(href[1:], known_ids, f"broken page anchor: {href}")

    def test_local_runtime_assets_exist(self):
        runtime_assets = self.parser.scripts + self.parser.stylesheets
        self.assertTrue(runtime_assets)
        for asset in runtime_assets:
            parsed = urlparse(asset)
            self.assertFalse(parsed.scheme, f"external runtime dependency: {asset}")
            self.assertTrue((ROOT / parsed.path).is_file(), f"missing runtime asset: {asset}")
        self.assertNotIn("googletagmanager", HTML)
        self.assertNotIn("gtag(", HTML)

    def test_catalog_matches_app_shape(self):
        self.assertEqual(len(self.parser.exercise_ids), 48)
        self.assertEqual(len(set(self.parser.exercise_ids)), 48)
        self.assertIn('data-cat="desk"', HTML)
        self.assertIn("Desk-ready <b>32</b>", HTML)

        floor_ids = {
            "bridges",
            "flutter-kicks",
            "crunches",
            "heel-taps",
            "climbers",
            "plank-hold",
            "shoulder-taps",
            "prone-reverse-fly",
            "w-extensions",
            "air-bike-crunches",
            "scissors",
            "crunch-kicks",
            "plank-rotations",
            "reverse-angels",
            "raised-leg-circles",
            "plank-leg-raises",
        }
        for exercise_id in floor_ids:
            self.assertIn(f'"{exercise_id}"', SCRIPT)
        self.assertIn('card.id === "stretches" ? "15 sec" : "10 sec"', SCRIPT)
        timed_badges = re.findall(r'<span class="illo-dur">(\d+) sec</span>', HTML)
        self.assertTrue(timed_badges)
        self.assertEqual(set(timed_badges), {"10", "15"})

    def test_current_product_promises_are_present(self):
        for promise in (
            "Fully offline",
            "No countdown",
            "Floor movements stay out unless you opt in",
            "100",
            "breaks, minutes",
            "no accounts, analytics, sign-up, or network calls",
        ):
            self.assertIn(promise, HTML)

    def test_machine_readable_files_are_valid(self):
        manifest = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "Exercise 1 Min")
        self.assertEqual(manifest["lang"], "en-US")

        marker = '<script type="application/ld+json">'
        start = HTML.index(marker) + len(marker)
        end = HTML.index("</script>", start)
        structured_data = json.loads(HTML[start:end])
        self.assertEqual(structured_data["@context"], "https://schema.org")


if __name__ == "__main__":
    unittest.main()
