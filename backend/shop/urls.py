from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views as v
r = DefaultRouter()
r.register("categories", v.CategoryViewSet, "category"); r.register("products", v.ProductViewSet, "product"); r.register("shops", v.ShopViewSet, "shop")
r.register("cart", v.CartViewSet, "cart"); r.register("wishlist", v.WishlistViewSet, "wishlist")
r.register("addresses", v.AddressViewSet, "address"); r.register("orders", v.OrderViewSet, "order")
r.register("admin/products", v.AdminProductViewSet, "admin-product"); r.register("admin/orders", v.AdminOrderViewSet, "admin-order")
urlpatterns = [path("auth/register/", v.register), path("auth/login/", v.login), path("auth/logout/", v.logout),
    path("payments/initiate/", v.payment_initiate), path("payments/verify/", v.payment_verify), path("admin/stats/", v.admin_stats), path("", include(r.urls))]
