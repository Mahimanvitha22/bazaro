from django.conf import settings
from django.db import models
U = settings.AUTH_USER_MODEL
class Category(models.Model):
    name = models.CharField(max_length=80, unique=True); slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    def __str__(self): return self.name
class Shop(models.Model):
    name = models.CharField(max_length=120, unique=True); locality = models.CharField(max_length=80)
    tagline = models.CharField(max_length=200, blank=True); rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    image = models.ImageField(upload_to="shops/", blank=True)
    def __str__(self): return self.name
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    shop = models.ForeignKey(Shop, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    name = models.CharField(max_length=160); description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2); stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True); rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    sold = models.PositiveIntegerField(default=0); is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False); created = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
class CartItem(models.Model):
    user = models.ForeignKey(U, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE); quantity = models.PositiveIntegerField(default=1)
    class Meta: unique_together = ("user", "product")
class WishlistItem(models.Model):
    user = models.ForeignKey(U, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    class Meta: unique_together = ("user", "product")
class Address(models.Model):
    user = models.ForeignKey(U, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=120); phone = models.CharField(max_length=20)
    line1 = models.CharField(max_length=200); city = models.CharField(max_length=80)
    state = models.CharField(max_length=80); pincode = models.CharField(max_length=12)
    def __str__(self): return f"{self.full_name}, {self.line1}, {self.city} {self.pincode}"
class Order(models.Model):
    STATUS = [("pending","Pending payment"),("paid","Paid"),("shipped","Shipped"),("delivered","Delivered"),("cancelled","Cancelled")]
    user = models.ForeignKey(U, on_delete=models.PROTECT, related_name="orders")
    shipping_address = models.TextField()  # snapshot
    status = models.CharField(max_length=12, choices=STATUS, default="pending")
    total = models.DecimalField(max_digits=12, decimal_places=2); created = models.DateTimeField(auto_now_add=True)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=160); price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot
    quantity = models.PositiveIntegerField()
class Payment(models.Model):
    STATUS = [("created","Created"),("success","Success"),("failed","Failed")]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    razorpay_order_id = models.CharField(max_length=80); razorpay_payment_id = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="created"); is_demo = models.BooleanField(default=False)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/"); alt = models.CharField(max_length=160, blank=True)
    class Meta: ordering = ["id"]
