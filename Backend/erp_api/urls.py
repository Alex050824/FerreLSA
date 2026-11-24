from django.urls import re_path

from . import inventory, payments, purchases, sales, users
from .db import query
from .http import endpoint, response


@endpoint("GET")
def health(request):
    query("SELECT 1")
    return response({"estado": "ok"})

@endpoint("GET", access="ADMIN")
def comments(request):
    return response(query("SELECT * FROM comentarios_productos ORDER BY fecha DESC, id DESC"))


urlpatterns = [
    re_path(r"^salud/?$", health),
    re_path(r"^admin/comentarios/?$", comments),
    re_path(r"^auth/registro/?$", users.register),
    re_path(r"^auth/login/?$", users.login),
    re_path(r"^auth/logout/?$", users.logout),
    re_path(r"^usuarios/me/?$", users.profile),
    re_path(r"^usuarios/?$", users.users),
    re_path(r"^usuarios/(?P<pk>[0-9]+)/?$", users.user_detail),
    re_path(r"^categorias/?$", inventory.categories),
    re_path(r"^productos/?$", inventory.products),
    re_path(r"^productos/(?P<pk>[0-9]+)/?$", inventory.product_detail),
    re_path(r"^admin/(?P<resource>categorias|proveedores|productos)/?$", inventory.catalog),
    re_path(r"^admin/(?P<resource>categorias|proveedores|productos)/(?P<pk>[0-9]+)/?$", inventory.catalog_detail),
    re_path(r"^inventario/movimientos/?$", inventory.movements),
    re_path(r"^compras/?$", purchases.purchases),
    re_path(r"^compras/(?P<pk>[0-9]+)/?$", purchases.purchase_detail),
    re_path(r"^compras/(?P<pk>[0-9]+)/recibir/?$", purchases.transition, {"status": "RECIBIDA"}),
    re_path(r"^compras/(?P<pk>[0-9]+)/cancelar/?$", purchases.transition, {"status": "CANCELADA"}),
    re_path(r"^ventas/?$", sales.sales),
    re_path(r"^ventas/(?P<pk>[0-9]+)/?$", sales.sale_detail),
    re_path(r"^ventas/(?P<pk>[0-9]+)/comprobante/?$", sales.receipt),
    re_path(r"^ventas/(?P<pk>[0-9]+)/nota-credito/?$", sales.refund),
    re_path(r"^integraciones/paypal/ventas/(?P<pk>[0-9]+)/confirmar/?$", payments.confirm),
    re_path(r"^integraciones/paypal/ventas/(?P<pk>[0-9]+)/cancelar/?$", payments.cancel),
]
