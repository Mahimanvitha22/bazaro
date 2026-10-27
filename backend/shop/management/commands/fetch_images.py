"""Attach photos to categories, shops and products that have NO image. Never overwrites existing images.
1) uses backend/seed_images/<slug>.(jpg|png|webp) if present; 2) else searches Wikimedia Commons, keeping only
openly licensed (CC / public domain) results and logging credits in seed_images/ATTRIBUTION.txt. Needs internet.
Matches can be imperfect: review them and replace via /admin/ or by dropping a file into seed_images/."""
import json, re, urllib.parse, urllib.request
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from shop.models import Category, Product, Shop
DIR = Path(settings.BASE_DIR) / "seed_images"
CAT = {"fashion": "Indian ethnic clothing", "decor": "Indian handicrafts", "electronics": "consumer electronics gadgets",
       "groceries": "Indian spices market", "kitchen": "Indian kitchen utensils", "beauty": "ayurvedic herbal oil"}
SHOP = {"Kondapalli Toys & Crafts": "Kondapalli toys", "Machilipatnam Kalamkari House": "Kalamkari textile",
        "Guntur Spice & Coffee Traders": "spices coffee beans", "Benz Circle Gadget Hub": "electronics shop"}
UA = {"User-Agent": "BazaroSeed/1.0 (local development)"}
def fetch(url): return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
def term(obj):
    if isinstance(obj, Category): return CAT.get(obj.slug, obj.name)
    if isinstance(obj, Shop): return SHOP.get(obj.name, obj.name)
    return re.sub(r"\b\d+\s*(kg|g|l|ml|w|mah)\b|\d+", "", obj.name, flags=re.I).strip()
class Command(BaseCommand):
    def attach(self, obj):
        slug = re.sub(r"[^a-z0-9]+", "-", (obj.slug if isinstance(obj, Category) else obj.name).lower()).strip("-")
        local = next((f for e in ("jpg", "jpeg", "png", "webp") if (f := DIR / f"{slug}.{e}").exists()), None)
        if local: obj.image.save(local.name, ContentFile(local.read_bytes()), save=True); return self.stdout.write(f"{obj}: local file")
        q = urllib.parse.urlencode({"action": "query", "generator": "search", "gsrnamespace": 6, "gsrlimit": 10, "gsrsearch": term(obj), "prop": "imageinfo",
                                    "iiprop": "url|mime|extmetadata", "iiurlwidth": 800, "format": "json"})
        pages = json.loads(fetch("https://commons.wikimedia.org/w/api.php?" + q)).get("query", {}).get("pages", {}).values()
        for pg in sorted(pages, key=lambda x: x.get("index", 99)):
            info = pg["imageinfo"][0]; meta = info.get("extmetadata", {}); lic = meta.get("LicenseShortName", {}).get("value", "")
            if info["mime"] not in ("image/jpeg", "image/png") or not re.search(r"cc|public domain|pd", lic, re.I): continue
            obj.image.save(f"{slug}.jpg" if info["mime"] == "image/jpeg" else f"{slug}.png", ContentFile(fetch(info["thumburl"])), save=True)
            artist = re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "unknown"))
            with open(DIR / "ATTRIBUTION.txt", "a") as f: f.write(f"{obj}: {pg['title']} by {artist} ({lic}) {info['descriptionurl']}\n")
            return self.stdout.write(f"{obj}: {pg['title']} ({lic})")
        self.stdout.write(f"{obj}: no suitable open image; add {slug}.jpg to seed_images/")
    def handle(self, *a, **k):
        DIR.mkdir(exist_ok=True)
        for qs in (Category.objects.filter(image=""), Shop.objects.filter(image=""), Product.objects.filter(image="")):
            for o in qs:
                try: self.attach(o)
                except Exception as e: self.stdout.write(f"{o}: failed ({e})")
