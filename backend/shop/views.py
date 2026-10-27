import hmac, hashlib, uuid
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, mixins, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import *
from .serializers import *

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    s = RegisterSerializer(data=request.data); s.is_valid(raise_exception=True); u = s.save()
    return Response({"token": Token.objects.get_or_create(user=u)[0].key, "username": u.username}, 201)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login(request):
    u = authenticate(username=request.data.get("username"), password=request.data.get("password"))
    if not u: return Response({"detail": "Invalid username or password."}, 400)
    return Response({"token": Token.objects.get_or_create(user=u)[0].key, "username": u.username, "is_staff": u.is_staff})
@api_view(["POST"])
def logout(request):
    Token.objects.filter(user=request.user).delete(); return Response(status=204)

_active = Count("products", filter=Q(products__is_active=True))
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.annotate(product_count=_active).order_by("id"); serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]; pagination_class = None
class ShopViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Shop.objects.annotate(product_count=_active).order_by("-rating"); serializer_class = ShopSerializer
    permission_classes = [permissions.AllowAny]; pagination_class = None
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer; permission_classes = [permissions.AllowAny]
    def get_queryset(self):
        p = self.request.query_params; qs = Product.objects.filter(is_active=True).select_related("category", "shop").prefetch_related("images")
        if p.get("shop", "").isdigit(): qs = qs.filter(shop_id=int(p["shop"]))
        if p.get("q"):
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=p["q"]) | Q(description__icontains=p["q"]))
        if p.get("category"): qs = qs.filter(category__slug=p["category"])
        try:
            if p.get("min_price"): qs = qs.filter(price__gte=Decimal(p["min_price"]))
            if p.get("max_price"): qs = qs.filter(price__lte=Decimal(p["max_price"]))
            if p.get("min_rating"): qs = qs.filter(rating__gte=Decimal(p["min_rating"]))
        except Exception: pass
        if p.get("in_stock") == "true": qs = qs.filter(stock__gt=0)
        if p.get("featured") == "true": qs = qs.filter(featured=True)
        order = {"price_asc": "price", "price_desc": "-price", "popular": "-sold", "rating": "-rating", "newest": "-created"}
        return qs.order_by(order.get(p.get("ordering"), "-created"))
    @action(detail=True, methods=["get"], pagination_class=None)
    def similar(self, request, pk=None):
        """Up to 8 products: same category first, topped up from other categories."""
        prod = self.get_object(); N = 8
        base = Product.objects.filter(is_active=True).exclude(pk=prod.pk).select_related("category").prefetch_related("images").order_by("-rating", "-sold")
        same = list(base.filter(category=prod.category)[:N])
        rest = list(base.exclude(category=prod.category)[:N - len(same)]) if len(same) < N else []
        return Response(self.get_serializer(same + rest, many=True).data)

class OwnedViewSet(viewsets.ModelViewSet):
    def get_queryset(self): return self.queryset.filter(user=self.request.user)
    def perform_create(self, s): s.save(user=self.request.user)
class CartViewSet(OwnedViewSet):
    queryset = CartItem.objects.select_related("product"); serializer_class = CartItemSerializer; pagination_class = None
    def create(self, request, *a, **k):
        s = self.get_serializer(data=request.data); s.is_valid(raise_exception=True)
        prod, qty = s.validated_data["product"], s.validated_data["quantity"]
        item, _ = CartItem.objects.get_or_create(user=request.user, product=prod, defaults={"quantity": 0})
        if item.quantity + qty > prod.stock:
            if not item.quantity: item.delete()
            return Response({"detail": f"Only {prod.stock} in stock."}, 400)
        item.quantity += qty; item.save()
        return Response(self.get_serializer(item).data, 201)
    def update(self, request, *a, **k):
        item = self.get_object(); q = int(request.data.get("quantity", 0))
        if q < 1 or q > item.product.stock: return Response({"detail": f"Quantity must be 1-{item.product.stock}."}, 400)
        item.quantity = q; item.save(); return Response(self.get_serializer(item).data)
    partial_update = update
class WishlistViewSet(OwnedViewSet):
    queryset = WishlistItem.objects.select_related("product"); serializer_class = WishlistSerializer; pagination_class = None
class AddressViewSet(OwnedViewSet):
    queryset = Address.objects.all(); serializer_class = AddressSerializer; pagination_class = None

class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    def get_queryset(self): return Order.objects.filter(user=self.request.user).prefetch_related("items").order_by("-created")
    @transaction.atomic
    def create(self, request):
        addr = Address.objects.filter(user=request.user, pk=request.data.get("address_id")).first()
        if not addr: return Response({"detail": "Choose a valid shipping address."}, 400)
        items = list(CartItem.objects.filter(user=request.user))
        if not items: return Response({"detail": "Your cart is empty."}, 400)
        prods = {p.id: p for p in Product.objects.select_for_update().filter(id__in=[i.product_id for i in items])}
        total = Decimal("0")
        for i in items:
            p = prods[i.product_id]
            if not p.is_active or p.stock < i.quantity: return Response({"detail": f"'{p.name}' has only {p.stock} left."}, 400)
            total += p.price * i.quantity  # server-side total
        order = Order.objects.create(user=request.user, shipping_address=str(addr), total=total)
        for i in items:
            p = prods[i.product_id]; p.stock -= i.quantity; p.sold += i.quantity; p.save()
            OrderItem.objects.create(order=order, product=p, name=p.name, price=p.price, quantity=i.quantity)
        CartItem.objects.filter(user=request.user).delete()
        return Response(OrderSerializer(order).data, 201)

def _sign(order_id, payment_id): return hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
@api_view(["POST"])
def payment_initiate(request):
    order = Order.objects.filter(user=request.user, pk=request.data.get("order_id"), status="pending").first()
    if not order: return Response({"detail": "Order not found or not awaiting payment."}, 404)
    if settings.DEMO_PAYMENTS: rid = "demo_" + uuid.uuid4().hex[:12]
    else:
        import razorpay
        rid = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)).order.create(
            {"amount": int(order.total * 100), "currency": "INR", "receipt": f"order_{order.id}"})["id"]
    Payment.objects.update_or_create(order=order, defaults={"razorpay_order_id": rid, "status": "created", "is_demo": settings.DEMO_PAYMENTS})
    return Response({"razorpay_order_id": rid, "amount": int(order.total * 100), "key": settings.RAZORPAY_KEY_ID, "demo": settings.DEMO_PAYMENTS})
@api_view(["POST"])
def payment_verify(request):
    pay = Payment.objects.select_related("order").filter(order__user=request.user, order_id=request.data.get("order_id")).first()
    if not pay or pay.order.status != "pending": return Response({"detail": "Nothing to verify."}, 404)
    pid = request.data.get("razorpay_payment_id", "")
    if pay.is_demo: ok = bool(request.data.get("demo_confirm"))  # only reachable when no real keys are configured
    else:
        ok = pay.razorpay_order_id == request.data.get("razorpay_order_id") and hmac.compare_digest(
            _sign(pay.razorpay_order_id, pid), str(request.data.get("razorpay_signature", "")))
    pay.razorpay_payment_id = pid; pay.status = "success" if ok else "failed"; pay.save()
    if ok: pay.order.status = "paid"; pay.order.save()
    return Response({"status": pay.status}, 200 if ok else 400)

class AdminProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all(); serializer_class = ProductSerializer; permission_classes = [permissions.IsAdminUser]
class AdminOrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Order.objects.all().order_by("-created"); serializer_class = OrderSerializer; permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "patch"]
@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def admin_stats(request):
    paid = Order.objects.exclude(status__in=["pending", "cancelled"])
    return Response({"orders": Order.objects.count(), "paid_orders": paid.count(), "revenue": paid.aggregate(t=Sum("total"))["t"] or 0,
                     "customers": request.user.__class__.objects.filter(is_staff=False).count()})
