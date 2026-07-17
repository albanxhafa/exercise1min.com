import json
import re
import struct
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "assets/js/app.js").read_text(encoding="utf-8")
LLMS = (ROOT / "llms.txt").read_text(encoding="utf-8")
LLMS_FULL = (ROOT / "llms-full.txt").read_text(encoding="utf-8")


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.images = []
        self.scripts = []
        self.stylesheets = []
        self.exercise_ids = []
        self.meta = {}
        self.link_elements = []
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
        if tag == "meta":
            key = values.get("property") or values.get("name")
            if key:
                self.meta[key] = values.get("content")
        if tag == "link":
            self.link_elements.append(values)
            if values.get("rel") == "stylesheet":
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
        for icon in manifest["icons"]:
            self.assertTrue((ROOT / icon["src"].lstrip("/")).is_file())

        marker = '<script type="application/ld+json">'
        start = HTML.index(marker) + len(marker)
        end = HTML.index("</script>", start)
        structured_data = json.loads(HTML[start:end])
        self.assertEqual(structured_data["@context"], "https://schema.org")

        graph = structured_data["@graph"]
        types = {item["@type"]: item for item in graph}
        app = types["MobileApplication"]
        self.assertNotIn("offers", app, "pre-launch app must not advertise an available offer")
        self.assertNotIn("isAccessibleForFree", app)
        self.assertEqual(app["operatingSystem"], "iOS, Android")
        self.assertEqual(len(types["ItemList"]["itemListElement"]), 48)
        self.assertEqual(
            types["WebPage"]["primaryImageOfPage"]["url"],
            "https://exercise1min.com/assets/img/exercise1min-social-card.png",
        )
        for item in graph:
            if "@id" in item:
                self.assertTrue(item["@id"].startswith("https://exercise1min.com/"))

    def test_search_and_social_metadata_are_consistent(self):
        canonical = next(
            link["href"]
            for link in self.parser.link_elements
            if link.get("rel") == "canonical"
        )
        self.assertEqual(canonical, "https://exercise1min.com/")
        self.assertEqual(self.parser.meta["og:url"], canonical)
        self.assertEqual(self.parser.meta["twitter:card"], "summary_large_image")

        social_image = "https://exercise1min.com/assets/img/exercise1min-social-card.png"
        self.assertEqual(self.parser.meta["og:image"], social_image)
        self.assertEqual(self.parser.meta["twitter:image"], social_image)
        self.assertEqual(self.parser.meta["og:image:width"], "1200")
        self.assertEqual(self.parser.meta["og:image:height"], "630")
        self.assertTrue(self.parser.meta["og:image:alt"])
        self.assertTrue(self.parser.meta["twitter:image:alt"])

        image_path = ROOT / "assets/img/exercise1min-social-card.png"
        with image_path.open("rb") as image:
            header = image.read(24)
        self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", header[16:24]), (1200, 630))

        alternates = {
            link.get("href"): link.get("type")
            for link in self.parser.link_elements
            if link.get("rel") == "alternate"
        }
        self.assertEqual(alternates["/llms.txt"], "text/plain")
        self.assertEqual(alternates["/llms-full.txt"], "text/plain")

    def test_crawl_discovery_files_are_consistent(self):
        sitemap = ET.parse(ROOT / "sitemap.xml")
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = sitemap.findall("sm:url", namespace)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].findtext("sm:loc", namespaces=namespace), "https://exercise1min.com/")
        self.assertRegex(
            urls[0].findtext("sm:lastmod", namespaces=namespace),
            r"^\d{4}-\d{2}-\d{2}$",
        )

        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://exercise1min.com/sitemap.xml", robots)

    def test_llm_references_are_current_and_complete(self):
        self.assertTrue(LLMS.startswith("# Exercise 1 Min\n\n> "))
        self.assertIn("https://exercise1min.com/", LLMS)
        self.assertIn("not yet available to download", LLMS)
        self.assertIn("## Optional", LLMS)

        sections = re.split(r"(?m)^## ", LLMS)[1:]
        for section in sections:
            nonempty = [line for line in section.splitlines()[1:] if line.strip()]
            self.assertTrue(nonempty)
            self.assertTrue(
                all(line.startswith("- [") for line in nonempty),
                f"llms.txt H2 sections must contain link lists: {section.splitlines()[0]}",
            )

        self.assertIn("Updated: 2026-07-17", LLMS_FULL)
        self.assertIn("Move for a minute. Keep your momentum.", LLMS_FULL)
        self.assertNotIn("One minute of exercise, on repeat.", LLMS_FULL)
        self.assertIn("English at launch; Albanian is not currently included.", LLMS_FULL)

        marker = '<script type="application/ld+json">'
        start = HTML.index(marker) + len(marker)
        end = HTML.index("</script>", start)
        graph = json.loads(HTML[start:end])["@graph"]
        item_list = next(item for item in graph if item["@type"] == "ItemList")
        exercise_names = [item["name"] for item in item_list["itemListElement"]]
        self.assertEqual(len(exercise_names), 48)
        for name in exercise_names:
            self.assertIn(name, LLMS_FULL)


if __name__ == "__main__":
    unittest.main()
