# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from freezegun import freeze_time

from odoo.tests import tagged

from .test_purchase import TestStockReceptionInProgress


@tagged("post_install", "-at_install")
class TestReceptionInProgressCurrency(TestStockReceptionInProgress):
    """Foreign currency purchase: the reception in progress invoice is posted
    at one exchange rate and the goods are received later, at another one.

    The goods in transit account (327) is debited by the invoice at the
    invoice rate; every reception must move that same value into stock
    (371), so that 327 ends at zero once everything is received, whatever
    the rate on the reception date.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.currency.rate"].search(
            [
                ("currency_id", "=", cls.eur.id),
                ("company_id", "in", [False, cls.env.company.id]),
            ]
        ).unlink()
        # RON per EUR: 5.00 on the invoice, 5.50 / 4.50 on the receptions
        for day, ron_per_eur in (
            ("2026-01-10", 5.0),
            ("2026-01-20", 5.5),
            ("2026-01-30", 4.5),
        ):
            cls.env["res.currency.rate"].create(
                {
                    "name": day,
                    "currency_id": cls.eur.id,
                    "rate": 1 / ron_per_eur,
                    "company_id": cls.env.company.id,
                }
            )

    def _balance(self, account):
        lines = self.env["account.move.line"].search(
            [
                ("account_id", "=", account.id),
                ("company_id", "=", self.env.company.id),
                ("parent_state", "=", "posted"),
            ]
        )
        return round(sum(lines.mapped("balance")), 2)

    def _create_po_and_invoice(self, product, qty=10, price=100):
        with freeze_time("2026-01-10"):
            purchase = self.env["purchase.order"].create(
                {
                    "partner_id": self.supplier_1.id,
                    "currency_id": self.eur.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "product_qty": qty,
                                "price_unit": price,
                            },
                        )
                    ],
                }
            )
            purchase.button_confirm()
            purchase.action_create_reception_in_progress_invoice()
            invoice = purchase.invoice_ids
            invoice.invoice_date = "2026-01-10"
            invoice.action_post()
        return purchase, invoice

    def _receive(self, purchase, qty, day):
        with freeze_time(day):
            picking = purchase.picking_ids.filtered(
                lambda p: p.state not in ("done", "cancel")
            )
            picking.move_ids._set_quantity_done(qty)
            picking.move_ids.picked = True
            res = picking.button_validate()
            if isinstance(res, dict) and res.get("res_model") == (
                "stock.backorder.confirmation"
            ):
                self.env["stock.backorder.confirmation"].with_context(
                    **res["context"]
                ).create({}).process()
        return picking

    def _check(self, stock_value, transit_value, label):
        self.assertEqual(
            self._balance(self.account_valuation),
            stock_value,
            f"{label}: stock account (371)",
        )
        self.assertEqual(
            self._balance(self.acc_327), transit_value, f"{label}: 327"
        )

    def _run_full(self, product):
        purchase, _invoice = self._create_po_and_invoice(product)
        # 10 x 100 EUR x 5.00
        self._check(0, 5000, "after invoice")
        self._receive(purchase, 10, "2026-01-20")
        self._check(5000, 0, "after full reception at 5.50")

    def _run_partial(self, product):
        purchase, _invoice = self._create_po_and_invoice(product)
        self._check(0, 5000, "after invoice")
        self._receive(purchase, 5, "2026-01-20")
        self._check(2500, 2500, "after 5/10 received at 5.50")
        self._receive(purchase, 5, "2026-01-30")
        self._check(5000, 0, "after 10/10 received at 4.50")

    def test_currency_full_reception_fifo(self):
        self._run_full(self.product_fifo)

    def test_currency_full_reception_avg(self):
        self._run_full(self.product_avg)

    def test_currency_partial_reception_fifo(self):
        self._run_partial(self.product_fifo)

    def test_currency_partial_reception_avg(self):
        self._run_partial(self.product_avg)
