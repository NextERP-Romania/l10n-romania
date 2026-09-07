# Copyright (C) 2026 NextERP Romania
# Copyright (C) 2026 Dakai Soft SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from odoo.addons.l10n_ro_stock_account_retail.tests.common import TestRetailCommon


@tagged("post_install", "-at_install")
class TestRetailPos(TestRetailCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.company
        # Creating a payment method and a config is reserved to the POS
        # administrator; the accounting fixture user is not one.
        cls.env.user.group_ids |= cls.env.ref("point_of_sale.group_pos_manager")
        cls.cash_journal = cls.env["account.journal"].create(
            {
                "name": "Cash Shop",
                "type": "cash",
                "code": "CSHOP",
                "company_id": company.id,
            }
        )
        cls.payment_method = cls.env["pos.payment.method"].create(
            {
                "name": "Cash Shop",
                "journal_id": cls.cash_journal.id,
                "company_id": company.id,
            }
        )
        cls.pos_config = cls.env["pos.config"].create(
            {
                "name": "Magazin 1 POS",
                "company_id": company.id,
                "picking_type_id": cls.warehouse_mag1.pos_type_id.id,
                "payment_method_ids": [(6, 0, cls.payment_method.ids)],
            }
        )

    def _sell_through_pos(self, product, qty, price_unit):
        """Open a session, sell, pay and close it. Returns the session."""
        self.pos_config.open_ui()
        session = self.pos_config.current_session_id
        total = qty * price_unit
        order = self.env["pos.order"].create(
            {
                "company_id": self.env.company.id,
                "session_id": session.id,
                "partner_id": self.customer_1.id,
                "lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "qty": qty,
                            "price_unit": price_unit,
                            "price_subtotal": total,
                            "price_subtotal_incl": total,
                        },
                    )
                ],
                "amount_tax": 0.0,
                "amount_total": total,
                "amount_paid": 0.0,
                "amount_return": 0.0,
                "last_order_preparation_change": "{}",
            }
        )
        order.env["pos.make.payment"].with_context(
            active_ids=order.ids, active_id=order.id
        ).create({"amount": total, "payment_method_id": self.payment_method.id}).check()
        self.assertEqual(order.state, "paid")
        session.action_pos_session_closing_control()
        return session, order

    def test_closing_entry_does_not_discharge_the_stock_again(self):
        """The session closing entry must carry no stock lines.

        The Romanian stock accounting already posted the discharge on the
        stock move. Left alone, point of sale posts it a second time in the
        closing entry and the shop's 371 drifts by the value of everything it
        sold.
        """
        self._set_initial_stock(self.loc_mag1, self.product_retail, 10)
        session, order = self._sell_through_pos(self.product_retail, 2, 119.0)
        self.assertEqual(session.state, "closed")

        closing_accounts = session.move_id.line_ids.account_id
        self.assertNotIn(
            self.account_371_mag1,
            closing_accounts,
            "The closing entry discharged 371 a second time",
        )
        self.assertNotIn(
            self.account_607_mag1,
            closing_accounts,
            "The closing entry booked the cost of goods sold a second time",
        )

    def test_the_stock_move_still_discharges_once(self):
        """Neutralising the closing entry must not neutralise the discharge
        itself: the move keeps posting cost, markup and deferred VAT."""
        self._set_initial_stock(self.loc_mag1, self.product_retail, 10)
        _session, order = self._sell_through_pos(self.product_retail, 2, 119.0)

        moves = order.picking_ids.move_ids.filtered(
            lambda m: m.product_id == self.product_retail
        )
        self.assertTrue(moves, "The POS order created no stock move")

        cost_accounts = moves.account_move_id.line_ids.account_id
        self.assertIn(self.account_371_mag1, cost_accounts)
        self.assertIn(self.account_607_mag1, cost_accounts)

        markup_entry = self.env["account.move"].search(
            [("l10n_ro_extra_stock_move_id", "in", moves.ids)]
        )
        self.assertTrue(markup_entry, "No retail markup entry for the POS sale")
        self.assertEqual(
            sorted(
                (line.account_id.id, round(line.debit, 2), round(line.credit, 2))
                for line in markup_entry.line_ids
            ),
            sorted(
                [
                    (self.account_378_mag1.id, 100.0, 0.0),  # 2 * 50
                    (self.account_371_mag1.id, 0.0, 100.0),
                    (self.account_4428_mag1.id, 38.0, 0.0),  # 2 * 19
                    (self.account_371_mag1.id, 0.0, 38.0),
                ]
            ),
        )

    def test_ledger_records_the_pos_sale(self):
        """The sale has to leave the ledger, so the markup released is the
        one that was loaded."""
        self._set_initial_stock(self.loc_mag1, self.product_retail, 10)
        self._sell_through_pos(self.product_retail, 2, 119.0)
        markup, vat = self.env["l10n.ro.retail.markup.line"]._l10n_ro_carried(
            self.warehouse_mag1, self.product_retail, self.env.company
        )
        self.assertAlmostEqual(markup, 400.0, places=2)  # 500 loaded - 100 released
        self.assertAlmostEqual(vat, 152.0, places=2)  # 190 loaded - 38 released
