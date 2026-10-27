from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import Category, Product, Shop
CATS = [("Fashion & Ethnic", "fashion"), ("Handcrafted Decor", "decor"), ("Electronics & Gear", "electronics"),
        ("Farm-Fresh & Spices", "groceries"), ("Home & Kitchen", "kitchen"), ("Ayurvedic Beauty", "beauty")]
# Sample/fictional shops. (name, locality, tagline, rating)
SHOPS = [("Kondapalli Toys & Crafts", "Governorpet", "Hand-carved wooden toys and handicrafts.", 4.8),
         ("Machilipatnam Kalamkari House", "Labbipet", "Block-printed Kalamkari textiles and clothing.", 4.7),
         ("Guntur Spice & Coffee Traders", "Benz Circle", "Stone-ground spices, coffee and cold-pressed oils.", 4.6),
         ("Benz Circle Gadget Hub", "Benz Circle", "Everyday electronics and accessories.", 4.2)]
# (name, category idx, shop idx, price, mrp, stock, rating, featured)
P = [("Handloom Cotton Kurta",0,1,899,1099,20,4.5,0),("Block-Print Dupatta",0,1,549,649,35,4.2,0),("Kalamkari Cotton Saree",0,1,2499,2999,10,4.8,1),
 ("Ikat Cotton Shirt",0,1,1199,1399,18,4.3,0),("Handwoven Silk Stole",0,1,1490,1790,14,4.6,1),
 ("Kondapalli Wooden Toy Set",1,0,650,799,25,4.9,1),("Terracotta Tea Set",1,0,1299,1499,12,4.7,0),("Hand-painted Wall Plate",1,0,799,899,16,4.4,0),
 ("Bamboo Basket Trio",1,0,699,799,25,4.0,0),("Brass Diya Pair",1,0,450,550,40,4.5,0),
 ("Bluetooth Speaker",2,3,1799,2199,15,4.1,0),("Fast Charger 30W",2,3,799,999,40,4.3,0),("Wireless Earbuds",2,3,1499,1999,22,4.0,1),("Power Bank 10000mAh",2,3,1299,1599,30,4.2,0),
 ("Cold-Pressed Groundnut Oil 1L",3,2,349,399,60,4.6,1),("Guntur Chilli Powder 500g",3,2,199,229,80,4.4,0),("Stone-Ground Filter Coffee 500g",3,2,360,420,45,4.7,1),
 ("Turmeric Powder 250g",3,2,120,140,70,4.3,0),("Organic Jaggery 1kg",3,2,140,160,50,4.2,0),("Wild Forest Honey 500g",3,2,420,480,28,4.5,0),
 ("Cast Iron Dosa Tawa",4,0,1190,1390,15,4.6,0),("Copper Water Bottle",4,0,650,799,32,4.4,0),("Wooden Rolling Pin Set",4,0,399,499,26,4.1,0),("Stainless Steel Tiffin",4,0,899,1049,20,4.3,0),
 ("Almond & Saffron Body Oil",5,2,520,620,24,4.8,1),("Neem Soap Trio",5,2,249,299,60,4.2,0),("Kumkumadi Face Oil",5,2,899,1099,18,4.5,0),("Herbal Hair Oil",5,2,349,399,40,4.1,0)]
class Command(BaseCommand):
    help = "Load sample categories, shops and products. Safe to re-run; never touches existing images."
    def handle(self, *a, **k):
        cats = [Category.objects.get_or_create(slug=s, defaults={"name": n})[0] for n, s in CATS]
        shops = [Shop.objects.get_or_create(name=n, defaults={"locality": l, "tagline": t, "rating": r})[0] for n, l, t, r in SHOPS]
        for n, c, s, price, mrp, stock, rating, feat in P:
            d = dict(category=cats[c], shop=shops[s], price=price, mrp=mrp, stock=stock, rating=rating, featured=bool(feat), description=f"{n} from {shops[s].name}, {shops[s].locality}. Sample listing.")
            p, new = Product.objects.get_or_create(name=n, defaults=d)
            if not new and p.shop_id is None: Product.objects.filter(pk=p.pk).update(**d)  # adopt older sample rows, images untouched
        if not User.objects.filter(username="admin").exists(): User.objects.create_superuser("admin", "admin@example.com", "admin12345")
        self.stdout.write(f"Seeded {len(cats)} categories, {len(shops)} shops, {len(P)} products. Demo admin: admin / admin12345 (change it)")
