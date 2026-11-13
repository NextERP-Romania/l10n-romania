# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import CommonPosTest


@tagged("post_install", "-at_install")
class TestPosRetailShop(CommonPosTest):
    @classmethod
    @CommonPosTest.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)],
            limit=1,
        )
        cls.fiscal_position = cls.env["account.fiscal.position"].create(
            {"name": "Retail fiscal position", "company_id": cls.env.company.id}
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Retail pricelist",
                "currency_id": cls.env.company.currency_id.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.warehouse.write(
            {
                "l10n_ro_retail": True,
                "l10n_ro_fiscal_position_id": cls.fiscal_position.id,
                "l10n_ro_retail_pricelist_id": cls.pricelist.id,
            }
        )
        cls.pos_config_usd.picking_type_id = (
            cls.warehouse.pos_type_id or cls.warehouse.out_type_id
        )

    def test_config_uses_retail_shop_defaults(self):
        self.pos_config_usd.write(
            {
                "default_fiscal_position_id": False,
                "fiscal_position_ids": [(5, 0, 0)],
                "pricelist_id": False,
                "available_pricelist_ids": [(5, 0, 0)],
            }
        )

        values = self.pos_config_usd._l10n_ro_retail_shop_values()
        self.assertEqual(values["default_fiscal_position_id"], self.fiscal_position.id)
        self.assertEqual(values["pricelist_id"], self.pricelist.id)

        self.pos_config_usd._l10n_ro_apply_retail_shop()
        self.assertEqual(
            self.pos_config_usd.default_fiscal_position_id, self.fiscal_position
        )
        self.assertEqual(self.pos_config_usd.pricelist_id, self.pricelist)

    def test_explicit_pos_defaults_are_preserved(self):
        explicit_fiscal_position = self.env["account.fiscal.position"].create(
            {"name": "Explicit fiscal position", "company_id": self.env.company.id}
        )
        explicit_pricelist = self.env["product.pricelist"].create(
            {
                "name": "Explicit pricelist",
                "currency_id": self.env.company.currency_id.id,
                "company_id": self.env.company.id,
            }
        )
        self.pos_config_usd.write(
            {
                "default_fiscal_position_id": explicit_fiscal_position.id,
                "fiscal_position_ids": [(4, explicit_fiscal_position.id)],
                "pricelist_id": explicit_pricelist.id,
                "available_pricelist_ids": [(4, explicit_pricelist.id)],
            }
        )

        self.pos_config_usd._l10n_ro_apply_retail_shop()

        self.assertEqual(
            self.pos_config_usd.default_fiscal_position_id,
            explicit_fiscal_position,
        )
        self.assertEqual(self.pos_config_usd.pricelist_id, explicit_pricelist)
