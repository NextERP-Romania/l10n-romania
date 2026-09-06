# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from odoo.addons.l10n_ro_stock_account_retail.tests.common import TestRetailCommon


@tagged("post_install", "-at_install")
class TestRetailStockReport(TestRetailCommon):
    def _report_line(self, warehouse, product):
        return self.env["l10n.ro.stock.retail.report"].search(
            [
                ("warehouse_id", "=", warehouse.id),
                ("product_id", "=", product.id),
            ]
        )

    def test_report_shows_what_371_carries(self):
        """One row per (warehouse, product), split the way 371 is split.

        Ten units at a cost of 50 and a shelf price of 119 VAT included:
        500 of cost, 500 of markup, 190 of deferred VAT, 1190 on 371.
        """
        self._set_initial_stock(self.loc_mag1, self.product_retail, 10)
        row = self._report_line(self.warehouse_mag1, self.product_retail)
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.quantity, 10.0, places=2)
        self.assertAlmostEqual(row.cost_total, 500.0, places=2)
        self.assertAlmostEqual(row.markup_total, 500.0, places=2)
        self.assertAlmostEqual(row.vat_total, 190.0, places=2)
        self.assertAlmostEqual(row.retail_value, 1190.0, places=2)
        self.assertAlmostEqual(row.cost_unit, 50.0, places=2)
        self.assertAlmostEqual(row.retail_price_unit, 119.0, places=2)

    def test_nothing_to_revalue_when_the_price_has_not_moved(self):
        self._set_initial_stock(self.loc_mag1, self.product_retail, 10)
        row = self._report_line(self.warehouse_mag1, self.product_retail)
        self.assertAlmostEqual(row.current_price_unit, 119.0, places=2)
        self.assertAlmostEqual(row.price_gap_total, 0.0, places=2)

    def test_price_moved_without_a_document_shows_up_as_to_revalue(self):
        """The gap column is the point of the report: it names the amount a
        price change document still has to settle."""
        self._set_initial_stock(self.loc_mag1, self.product_retail, 10)
        self.env["product.pricelist.item"].with_context(
            skip_retail_price_change=True
        ).create(
            {
                "pricelist_id": self.pricelist_mag1.id,
                "applied_on": "0_product_variant",
                "product_id": self.product_retail.id,
                "compute_price": "fixed",
                "fixed_price": 178.5,
            }
        )
        row = self._report_line(self.warehouse_mag1, self.product_retail)
        self.assertAlmostEqual(row.current_price_unit, 178.5, places=2)
        # 10 * 178.50 wanted against 1190 carried
        self.assertAlmostEqual(row.price_gap_total, 595.0, places=2)

    def test_sold_out_products_leave_the_report(self):
        """A product the shop no longer holds carries nothing on 371, so it
        has no line - the view only keeps positive quantities."""
        self._set_initial_stock(self.loc_mag1, self.product_retail, 4)
        self._do_sale_delivery(self.warehouse_mag1, self.product_retail, 4, 119.0)
        self.assertFalse(self._report_line(self.warehouse_mag1, self.product_retail))

    def test_each_shop_reports_its_own_stock(self):
        """Two shops holding the same product are two rows, each with the
        markup its own pricelist loaded."""
        self.env["product.pricelist.item"].with_context(
            skip_retail_price_change=True
        ).create(
            {
                "pricelist_id": self.pricelist_mag2.id,
                "applied_on": "0_product_variant",
                "product_id": self.product_retail.id,
                "compute_price": "fixed",
                "fixed_price": 238.0,  # 200 net, so a markup of 150 a unit
            }
        )
        self._set_initial_stock(self.loc_mag1, self.product_retail, 10)
        self._set_initial_stock(self.loc_mag2, self.product_retail, 10)
        row1 = self._report_line(self.warehouse_mag1, self.product_retail)
        row2 = self._report_line(self.warehouse_mag2, self.product_retail)
        self.assertAlmostEqual(row1.markup_total, 500.0, places=2)
        self.assertAlmostEqual(row2.markup_total, 1500.0, places=2)
