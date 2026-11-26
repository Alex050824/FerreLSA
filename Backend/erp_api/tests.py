import json
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from .inventory import product_comments
from .reports import _power_bi_embed_url, power_bi_report
from .users import register


class ProductCommentsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("Backend.erp_api.inventory.query")
    @patch("Backend.erp_api.inventory.one", return_value={"id": 3})
    def test_public_list_uses_product_id(self, lookup, query):
        query.return_value = [{"id": 4, "comentario": "Bueno"}]
        result = product_comments(self.factory.get("/api/productos/3/comentarios"), "3")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(query.call_args.args[1], (3,))

    def test_create_is_not_supported(self):
        request = self.factory.post("/api/productos/3/comentarios", '{"comentario":"Bueno"}', content_type="application/json")
        result = product_comments(request, "3")
        self.assertEqual(result.status_code, 405)


class RegistrationTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("Backend.erp_api.users.save_user")
    def test_registration_creates_customer(self, save_user):
        save_user.return_value = {"id": 1, "rol": "CLIENTE", "correo": "cliente@example.com"}
        request = self.factory.post(
            "/api/auth/registro", {"nombre": "Cliente", "correo": "cliente@example.com", "password": "segura123"},
            content_type="application/json",
        )
        result = register(request)
        self.assertEqual(result.status_code, 201)
        self.assertEqual(save_user.call_args.args[0]["rol"], "CLIENTE")

    @patch("Backend.erp_api.users.save_user")
    def test_registration_rejects_role_and_short_password(self, save_user):
        for payload in (
            {"nombre": "Cliente", "correo": "cliente@example.com", "password": "segura123", "rol": "ADMIN"},
            {"nombre": "Cliente", "correo": "cliente@example.com", "password": "corta"},
        ):
            with self.subTest(payload=payload):
                result = register(self.factory.post("/api/auth/registro", payload, content_type="application/json"))
                self.assertEqual(result.status_code, 422)
        save_user.assert_not_called()


class PowerBIReportTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_only_power_bi_https_embed_urls_are_accepted(self):
        self.assertTrue(_power_bi_embed_url("https://app.powerbi.com/view?r=sample"))
        self.assertTrue(_power_bi_embed_url("https://app.powerbi.com/reportEmbed?reportId=sample"))
        self.assertFalse(_power_bi_embed_url("http://app.powerbi.com/view?r=sample"))
        self.assertFalse(_power_bi_embed_url("https://example.com/view?r=sample"))

    @patch("Backend.erp_api.users.authenticate", return_value={"rol": "CLIENTE"})
    def test_report_configuration_rejects_non_admin_users(self, authenticate):
        response = power_bi_report(self.factory.get("/api/admin/reportes/power-bi"))
        self.assertEqual(response.status_code, 403)

    @patch("Backend.erp_api.users.authenticate", return_value={"rol": "ADMIN"})
    @override_settings(POWER_BI_REPORT_URL="https://app.powerbi.com/view?r=sample")
    def test_admin_can_read_configured_report_url(self, authenticate):
        result = power_bi_report(self.factory.get("/api/admin/reportes/power-bi"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.content), {
            "configured": True, "url": "https://app.powerbi.com/view?r=sample",
        })
