from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
class RegisterSerializer(serializers.ModelSerializer):
    class Meta: model = User; fields = ("username", "email", "password")
    extra_kwargs = {"password": {"write_only": True, "min_length": 8}}
    def create(self, d): return User.objects.create_user(**d)
class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)
    image = serializers.SerializerMethodField()
    class Meta: model = Category; fields = "__all__"
    def get_image(self, o):
        if not o.image: return None
        req = self.context.get("request")
        return req.build_absolute_uri(o.image.url) if req else o.image.url
class ShopSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)
    image = serializers.SerializerMethodField()
    class Meta: model = Shop; fields = "__all__"
    def get_image(self, o):
        if not o.image: return None
        req = self.context.get("request")
        return req.build_absolute_uri(o.image.url) if req else o.image.url
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True, default=None)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    in_stock = serializers.SerializerMethodField(); gallery = serializers.SerializerMethodField()
    class Meta: model = Product; fields = "__all__"
    def get_gallery(self, o):
        req = self.context.get("request"); urls = ([o.image.url] if o.image else []) + [i.image.url for i in o.images.all()]
        return [req.build_absolute_uri(u) if req else u for u in urls]
    def get_in_stock(self, o): return o.stock > 0
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True); product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True), source="product", write_only=True)
    class Meta: model = CartItem; fields = ("id", "product", "product_id", "quantity")
    def validate_quantity(self, q):
        if q < 1: raise serializers.ValidationError("Quantity must be at least 1.")
        return q
class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True); product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True), source="product", write_only=True)
    class Meta: model = WishlistItem; fields = ("id", "product", "product_id")
class AddressSerializer(serializers.ModelSerializer):
    class Meta: model = Address; exclude = ("user",)
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta: model = OrderItem; fields = ("name", "price", "quantity")
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True); payment_status = serializers.CharField(source="payment.status", read_only=True, default=None)
    class Meta: model = Order; fields = ("id", "status", "total", "shipping_address", "created", "items", "payment_status")
