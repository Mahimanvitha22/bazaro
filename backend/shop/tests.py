import hashlib, hmac
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APITestCase
from .models import *
class ShopTests(APITestCase):
    def setUp(self):
        self.c = Category.objects.create(name="Toys", slug="toys")
        self.p = Product.objects.create(category=self.c, name="Top", price=Decimal("10.50"), stock=3)
        self.u = User.objects.create_user("a", password="pass12345"); self.v = User.objects.create_user("b", password="pass12345")
        self.addr = Address.objects.create(user=self.u, full_name="A", phone="1", line1="x", city="y", state="z", pincode="1")
    def test_register_login(self):
        self.assertEqual(self.client.post("/api/auth/register/", {"username": "n", "password": "pass12345"}).status_code, 201)
        self.assertIn("token", self.client.post("/api/auth/login/", {"username": "n", "password": "pass12345"}).data)
    def test_list_and_filter(self):
        self.assertEqual(self.client.get("/api/products/?q=top&in_stock=true").data["count"], 1)
        self.assertEqual(self.client.get("/api/products/?min_price=50").data["count"], 0)
    def test_cart_and_unauthenticated(self):
        self.assertEqual(self.client.get("/api/cart/").status_code, 401)
        self.client.force_authenticate(self.u)
        r = self.client.post("/api/cart/", {"product_id": self.p.id, "quantity": 2}); self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.post("/api/cart/", {"product_id": self.p.id, "quantity": 2}).status_code, 400)
    def test_wishlist(self):
        self.client.force_authenticate(self.u)
        self.assertEqual(self.client.post("/api/wishlist/", {"product_id": self.p.id}).status_code, 201)
    def test_order_total_stock_ownership(self):
        self.client.force_authenticate(self.u); self.client.post("/api/cart/", {"product_id": self.p.id, "quantity": 2})
        r = self.client.post("/api/orders/", {"address_id": self.addr.id, "total": "1"}); self.assertEqual(r.status_code, 201)
        self.assertEqual(Decimal(r.data["total"]), Decimal("21.00")); self.p.refresh_from_db(); self.assertEqual(self.p.stock, 1)
        self.client.force_authenticate(self.v); self.assertEqual(self.client.get(f"/api/orders/{r.data['id']}/").status_code, 404)
        self.assertEqual(self.client.get("/api/admin/stats/").status_code, 403)
    @override_settings(DEMO_PAYMENTS=False, RAZORPAY_KEY_SECRET="s", RAZORPAY_KEY_ID="k")
    def test_payment_signature(self):
        o = Order.objects.create(user=self.u, shipping_address="x", total=5); Payment.objects.create(order=o, razorpay_order_id="o1")
        self.client.force_authenticate(self.u)
        bad = self.client.post("/api/payments/verify/", {"order_id": o.id, "razorpay_order_id": "o1", "razorpay_payment_id": "p1", "razorpay_signature": "bad"})
        self.assertEqual(bad.status_code, 400); o.refresh_from_db(); self.assertEqual(o.status, "pending")
        Payment.objects.filter(order=o).update(status="created")
        o.status = "pending"; o.save()
        sig = hmac.new(b"s", b"o1|p1", hashlib.sha256).hexdigest()
        ok = self.client.post("/api/payments/verify/", {"order_id": o.id, "razorpay_order_id": "o1", "razorpay_payment_id": "p1", "razorpay_signature": sig})
        self.assertEqual(ok.status_code, 200); o.refresh_from_db(); self.assertEqual(o.status, "paid")

class DetailTests(APITestCase):
    def setUp(self):
        a = Category.objects.create(name="A", slug="a"); b = Category.objects.create(name="B", slug="b")
        self.p = Product.objects.create(category=a, name="Main", price=5, stock=1)
        self.same = Product.objects.create(category=a, name="Same", price=5, stock=1)
        self.other = Product.objects.create(category=b, name="Other", price=5, stock=1)
        Product.objects.create(category=a, name="Hidden", price=5, stock=1, is_active=False)
    def test_detail_and_404(self):
        r = self.client.get(f"/api/products/{self.p.id}/"); self.assertEqual(r.status_code, 200); self.assertIn("gallery", r.data)
        self.assertEqual(self.client.get("/api/products/99999/").status_code, 404)
    def test_similar_excludes_self_inactive_and_fills_from_other_categories(self):
        names = [x["name"] for x in self.client.get(f"/api/products/{self.p.id}/similar/").data]
        self.assertEqual(names, ["Same", "Other"])

class ShopTests(APITestCase):
    def test_shops_and_shop_filter(self):
        c = Category.objects.create(name="C", slug="c"); s = Shop.objects.create(name="S", locality="L")
        Product.objects.create(category=c, shop=s, name="In", price=1, stock=1); Product.objects.create(category=c, name="Out", price=1, stock=1)
        self.assertEqual(self.client.get("/api/shops/").data[0]["product_count"], 1)
        self.assertEqual([x["name"] for x in self.client.get(f"/api/products/?shop={s.id}").data["results"]], ["In"])
        self.assertEqual(self.client.get("/api/shops/999/").status_code, 404)
