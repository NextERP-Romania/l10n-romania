# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import tagged

from .common import TestROStockCommon


@tagged("post_install", "-at_install")
class TestROStockFifoUom(TestROStockCommon):
    """FIFO on a move written in a secondary UoM.

    Two unit systems meet in the FIFO split. ``_run_fifo_layers`` and core's
    ``_split`` speak the product's **reference** UoM, while
    ``stock.move.quantity`` and ``product_uom_qty`` are expressed in the
    **move's** UoM. They coincide only when the move happens to use the
    reference UoM — which is what every other FIFO test here does, so the
    mismatch stayed invisible.

    Selling in dozens, boxes or pallets while stocking in units makes the two
    diverge, and the consistency check compared one against the other: a move
    of 1 dozen reported "shipping 12.0 but 1.0 was accounted for" and refused
    to validate. When the check happened to pass, the quantities written onto
    the split moves were still off by the conversion factor.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.out_type = cls.location.warehouse_id.out_type_id
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        # The product is stocked in units but may be moved in dozens.
        cls.product_fifo.uom_ids = [Command.link(cls.uom_dozen.id)]
        # A move can only hold a quantity at the "Product Unit" precision, in
        # its OWN UoM. Expressing a units-denominated remainder in dozens can
        # therefore be off by up to half a step: 0.005 dozen = 0.06 units. See
        # ``test_layer_boundary_leaves_a_subprecision_residue``.
        precision = cls.env["decimal.precision"].precision_get("Product Unit")
        cls.DOZEN_RESIDUE = cls.uom_dozen._compute_quantity(
            10**-precision, cls.uom_unit, round=False
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _receive(self, qty, price, index):
        """Receive ``qty`` units at ``price``/unit — one FIFO layer."""
        self.create_purchase(
            {
                "currency_id": self.ron,
                "partner_id": self.supplier_1,
                "product_id": self.product_fifo,
                "qty": qty,
                "stock_qty": qty,
                "inv_qty": qty,
                "price": price,
                "inv_price": price,
                "index": index,
            }
        )
        return self.env["stock.move"].search(
            [
                ("product_id", "=", self.product_fifo.id),
                ("is_in", "=", True),
                ("state", "=", "done"),
                ("location_dest_id", "=", self.location.id),
            ],
            order="id desc",
            limit=1,
        )

    def _qty_at_location(self):
        return self.product_fifo.with_context(
            location=self.location.id, strict=True
        ).qty_available

    def _make_delivery(self, qty, uom):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.customer_1.id,
                "picking_type_id": self.out_type.id,
                "location_id": self.location.id,
                "location_dest_id": self.customer_location.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": self.product_fifo.id,
                            "product_uom_qty": qty,
                            "product_uom": uom.id,
                            "location_id": self.location.id,
                            "location_dest_id": self.customer_location.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        return picking

    def _done_moves(self, picking):
        return picking.move_ids.filtered(
            lambda m: m.product_id == self.product_fifo and m.state == "done"
        )

    def _shipped_units(self, picking):
        """Everything the picking shipped, converted to the product's UoM."""
        return sum(
            move.product_uom._compute_quantity(
                move.quantity, self.product_fifo.uom_id, round=False
            )
            for move in self._done_moves(picking)
        )

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------
    def test_conversion_helpers_round_trip(self):
        """The two helpers are inverses, and they actually convert."""
        picking = self._make_delivery(2, self.uom_dozen)
        move = picking.move_ids

        self.assertAlmostEqual(move._l10n_ro_qty_to_product_uom(2), 24.0)
        self.assertAlmostEqual(move._l10n_ro_qty_from_product_uom(24), 2.0)
        self.assertAlmostEqual(
            move._l10n_ro_qty_from_product_uom(move._l10n_ro_qty_to_product_uom(7)),
            7.0,
        )
        # An explicit UoM overrides the move's own.
        self.assertAlmostEqual(
            move._l10n_ro_qty_to_product_uom(5, uom=self.uom_unit), 5.0
        )

    def test_split_uom_defaults_to_the_moves_own(self):
        """``_l10n_ro_fifo_split_uom`` reads the UoM core put in the split vals,
        and falls back to the original move's UoM when core did not force one."""
        picking = self._make_delivery(1, self.uom_dozen)
        move = picking.move_ids
        Move = self.env["stock.move"]

        self.assertEqual(Move._l10n_ro_fifo_split_uom(move, {}), self.uom_dozen)
        self.assertEqual(
            Move._l10n_ro_fifo_split_uom(move, {"product_uom": self.uom_unit.id}),
            self.uom_unit,
        )

    # ------------------------------------------------------------------
    # Single layer: the check used to reject a perfectly valid move
    # ------------------------------------------------------------------
    def test_dozen_delivery_within_one_layer(self):
        """One layer covers the whole dozen, so nothing is split off. Before the
        fix the consistency check still rejected it: it compared 1 (dozen, off
        the move) against 12 (units, off the stack)."""
        self._receive(20, 100, "uom_po_single")
        picking = self._make_delivery(1, self.uom_dozen)
        picking.move_ids._set_quantity_done(1)
        picking.move_ids.picked = True

        self.assertIs(picking.button_validate(), True)
        self.assertEqual(picking.state, "done")

        done_moves = self._done_moves(picking)
        self.assertEqual(len(done_moves), 1, "A single layer needs no split")
        self.assertAlmostEqual(self._shipped_units(picking), 12.0)
        self.assertAlmostEqual(
            sum(abs(value) for value in done_moves.mapped("value")),
            12 * 100,
            msg="12 units off the only layer, at 100 each",
        )
        self.assertAlmostEqual(self._qty_at_location(), 8.0)

    # ------------------------------------------------------------------
    # Two layers: the split has to be valued and sized per layer
    # ------------------------------------------------------------------
    def test_dozen_delivery_spanning_two_layers(self):
        """10 @ 100 then 10 @ 150, shipping 1 dozen = 12 units: the move must be
        split 10 + 2 across the layers and valued accordingly."""
        self._receive(10, 100, "uom_po1")
        self._receive(10, 150, "uom_po2")
        self.assertAlmostEqual(self._qty_at_location(), 20.0)

        picking = self._make_delivery(1, self.uom_dozen)
        picking.move_ids._set_quantity_done(1)
        picking.move_ids.picked = True

        self.assertIs(picking.button_validate(), True)
        self.assertEqual(picking.state, "done")

        done_moves = self._done_moves(picking)
        self.assertEqual(len(done_moves), 2, "Two layers, two moves")
        self.assertAlmostEqual(
            self._shipped_units(picking),
            12.0,
            delta=self.DOZEN_RESIDUE,
            msg="A dozen leaves, not 1 unit and not 24",
        )
        # 10 units off the first layer at 100, the rest off the second at 150.
        self.assertAlmostEqual(
            sum(abs(value) for value in done_moves.mapped("value")),
            10 * 100 + 2 * 150,
            delta=self.DOZEN_RESIDUE * 150,
            msg="Each layer keeps its own unit price",
        )
        self.assertAlmostEqual(self._qty_at_location(), 8.0, delta=self.DOZEN_RESIDUE)

    def test_split_move_quantities_are_in_their_own_uom(self):
        """Unit-level check on the split: each resulting move's ``quantity``,
        read in that move's own UoM, must add up to the shipped quantity."""
        self._receive(10, 100, "uom_split_po1")
        self._receive(10, 150, "uom_split_po2")
        picking = self._make_delivery(1, self.uom_dozen)
        move = picking.move_ids
        move._set_quantity_done(1)
        move.picked = True

        splitted = move._split_for_fifo_assignment()

        self.assertTrue(splitted, "Spanning two layers must split the move off")
        total_units = sum(
            m.product_uom._compute_quantity(
                m.quantity, self.product_fifo.uom_id, round=False
            )
            for m in move | splitted
        )
        self.assertAlmostEqual(
            total_units,
            12.0,
            delta=self.DOZEN_RESIDUE,
            msg="The remainder plus the splits equal the shipped dozen",
        )

    # ------------------------------------------------------------------
    # Shipping less than ordered, in dozens
    # ------------------------------------------------------------------
    def test_partial_pick_in_dozens_backorders_the_rest(self):
        """2 dozen ordered, 1 dozen picked: 12 units ship and the other dozen
        backorders. The ordered demand stays in dozens too."""
        self._receive(30, 100, "uom_partial_po")
        picking = self._make_delivery(2, self.uom_dozen)
        move = picking.move_ids
        move._set_quantity_done(1)
        move.picked = True

        action = picking.button_validate()
        self.assertEqual(action["res_model"], "stock.backorder.confirmation")
        wizard = (
            self.env[action["res_model"]].with_context(**action["context"]).create({})
        )
        wizard.process()

        self.assertEqual(picking.state, "done")
        self.assertAlmostEqual(self._shipped_units(picking), 12.0)

        backorder = self.env["stock.picking"].search(
            [("backorder_id", "=", picking.id)]
        )
        self.assertEqual(len(backorder), 1)
        self.assertAlmostEqual(
            sum(backorder.move_ids.mapped("product_uom_qty")),
            1.0,
            msg="One dozen is left to ship",
        )
        self.assertAlmostEqual(self._qty_at_location(), 18.0)

    def test_layer_boundary_leaves_a_subprecision_residue(self):
        """Known limitation, pinned deliberately.

        A FIFO layer boundary almost never falls on a whole number of the
        move's UoM. Ten units off a move written in dozens leaves two units,
        which is 0.1666... dozen — and core's ``_set_quantity`` only stores a
        quantity at the "Product Unit" precision, so it becomes 0.17 dozen,
        i.e. 2.04 units. Shipping a dozen out of two layers therefore moves
        12.04 units, not 12.

        The residue is bounded by the move UoM's own precision and is inherent
        to denominating a move in a coarser unit than the one the FIFO stack
        works in; removing it would mean re-denominating the remaining move in
        the product's reference UoM, which also changes the ordered demand core
        already wrote. Asserted here so the behaviour is visible and a later
        change to it is a deliberate one, not a surprise.
        """
        self._receive(10, 100, "uom_residue_po1")
        self._receive(10, 150, "uom_residue_po2")
        picking = self._make_delivery(1, self.uom_dozen)
        picking.move_ids._set_quantity_done(1)
        picking.move_ids.picked = True
        picking.button_validate()

        self.assertAlmostEqual(self._shipped_units(picking), 12.04)
        self.assertLess(
            abs(self._shipped_units(picking) - 12.0),
            self.DOZEN_RESIDUE,
            msg="The residue stays within one step of the move UoM precision",
        )
