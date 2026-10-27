"""
Download seed images for Bazaro from Unsplash CDN.
Run once from the backend/ directory:
    python download_seed_images.py
All images are free to use under the Unsplash License.
https://unsplash.com/license
"""
import ssl, urllib.request, time
from pathlib import Path

OUT = Path(__file__).parent / "seed_images"
OUT.mkdir(exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = {"User-Agent": "BazaroSeed/1.0"}

# slug -> Unsplash photo ID  (w=800 gives ~80-120 KB JPEG, good quality)
# Each photo was chosen to match the product it represents.
IMAGES = {
    # ── Categories ──────────────────────────────────────────────────────────
    "fashion":      "photo-1610030469983-98e550d6193c",  # Indian ethnic kurtas on rack
    "decor":        "photo-1558618666-fcd25c85cd64",  # handcrafted clay pots / decor
    "electronics":  "photo-1518770660439-4636190af475",  # circuit board / electronics
    "groceries":    "photo-1596040033229-a9821ebd058d",  # colorful Indian spices
    "kitchen":      "photo-1556909114-f6e7ad7d3136",  # kitchen utensils
    "beauty":       "photo-1608248543803-ba4f8c70ae0b",  # ayurvedic oils and herbs

    # ── Shops ────────────────────────────────────────────────────────────────
    "kondapalli-toys-crafts":           "photo-1566576912321-d58ddd7a6088",  # wooden toys
    "machilipatnam-kalamkari-house":    "photo-1610030469983-98e550d6193c",  # textile / fabric
    "guntur-spice-coffee-traders":      "photo-1596040033229-a9821ebd058d",  # spices
    "benz-circle-gadget-hub":           "photo-1518770660439-4636190af475",  # electronics

    # ── Fashion & Ethnic ─────────────────────────────────────────────────────
    "handloom-cotton-kurta":    "photo-1583391733956-6c78276477e2",  # cotton kurta
    "block-print-dupatta":      "photo-1610030469983-98e550d6193c",  # printed dupatta / fabric
    "kalamkari-cotton-saree":   "photo-1617627143750-d86bc21e42bb",  # kalamkari saree
    "ikat-cotton-shirt":        "photo-1598033129183-c4f50c736f10",  # ikat shirt
    "handwoven-silk-stole":     "photo-1558769132-cb1aea458c5e",  # silk stole / scarf

    # ── Handcrafted Decor ────────────────────────────────────────────────────
    "kondapalli-wooden-toy-set":  "photo-1566576912321-d58ddd7a6088",  # wooden toys
    "terracotta-tea-set":         "photo-1556909114-f6e7ad7d3136",  # terracotta / clay tea set
    "hand-painted-wall-plate":    "photo-1558618666-fcd25c85cd64",  # hand-painted plate
    "bamboo-basket-trio":         "photo-1595435934249-5df7ed86e1c0",  # bamboo baskets
    "brass-diya-pair":            "photo-1604423035574-1e3d2b9e5e5e",  # brass diyas / lamps

    # ── Electronics & Gear ───────────────────────────────────────────────────
    "bluetooth-speaker":      "photo-1608043152269-423dbba4e7e1",  # bluetooth speaker
    "fast-charger-30w":       "photo-1583863788434-e58a36330cf0",  # USB charger
    "wireless-earbuds":       "photo-1590658268037-6bf12165a8df",  # wireless earbuds
    "power-bank-10000mah":    "photo-1609091839311-d5365f9ff1c5",  # power bank

    # ── Farm-Fresh & Spices ──────────────────────────────────────────────────
    "cold-pressed-groundnut-oil-1l": "photo-1474979266404-7eaacbcd87c5",  # cooking oil bottle
    "guntur-chilli-powder-500g":     "photo-1596040033229-a9821ebd058d",  # red chilli powder
    "stone-ground-filter-coffee-500g": "photo-1447933601403-0c6688de566e",  # coffee beans/powder
    "turmeric-powder-250g":          "photo-1615485500704-8e990f9900f7",  # turmeric powder
    "organic-jaggery-1kg":           "photo-1601050690597-df0568f70950",  # jaggery block
    "wild-forest-honey-500g":        "photo-1587049352846-4a222e784d38",  # honey jar

    # ── Home & Kitchen ───────────────────────────────────────────────────────
    "cast-iron-dosa-tawa":    "photo-1585515320310-259814833e62",  # cast iron pan
    "copper-water-bottle":    "photo-1602143407151-7111542de6e8",  # copper bottle
    "wooden-rolling-pin-set": "photo-1556909114-f6e7ad7d3136",  # rolling pin / kitchen
    "stainless-steel-tiffin": "photo-1585515320310-259814833e62",  # steel tiffin / container

    # ── Ayurvedic Beauty ─────────────────────────────────────────────────────
    "almond-saffron-body-oil": "photo-1608248543803-ba4f8c70ae0b",  # cosmetic oil bottle
    "neem-soap-trio":          "photo-1556228578-8c89e6adf883",  # soap bars
    "kumkumadi-face-oil":      "photo-1608248543803-ba4f8c70ae0b",  # face oil amber bottle
    "herbal-hair-oil":         "photo-1526045612212-70caf35c14df",  # hair oil bottle
}

def download(slug, photo_id):
    dest = OUT / f"{slug}.jpg"
    if dest.exists():
        print(f"  skip  {slug}.jpg (exists)")
        return True
    url = f"https://images.unsplash.com/{photo_id}?w=800&q=82&fm=jpg&fit=crop"
    try:
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=20, context=ctx).read()
        if len(data) < 5000:
            print(f"  WARN  {slug}: response too small ({len(data)} bytes), skipping")
            return False
        dest.write_bytes(data)
        print(f"  ok    {slug}.jpg  ({len(data)//1024} KB)")
        return True
    except Exception as e:
        print(f"  FAIL  {slug}: {e}")
        return False

ok = fail = 0
for slug, pid in IMAGES.items():
    if download(slug, pid):
        ok += 1
    else:
        fail += 1
    time.sleep(0.15)   # be polite

print(f"\nDone: {ok} downloaded, {fail} failed.")
print(f"Images saved to: {OUT}")
