# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "l10n.ro.mixin"]

    l10n_ro_currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_l10n_ro_valued_fields",
        string="Currency",
        compute_sudo=True,  # See explanation for sudo in compute method,
    )
    l10n_ro_amount_untaxed = fields.Monetary(
        compute="_compute_l10n_ro_valued_fields",
        string="Untaxed Amount",
        compute_sudo=True,  # See explanation for sudo in compute method,
        currency_field="l10n_ro_currency_id",
    )
    l10n_ro_amount_tax = fields.Monetary(
        compute="_compute_l10n_ro_valued_fields",
        string="Taxes",
        compute_sudo=True,
        currency_field="l10n_ro_currency_id",
    )
    l10n_ro_amount_total = fields.Monetary(
        compute="_compute_l10n_ro_valued_fields",
        string="Total",
        compute_sudo=True,
        currency_field="l10n_ro_currency_id",
    )
    l10n_ro_is_internal = fields.Boolean(compute="_compute_l10n_ro_is_internal")

    def _l10n_ro_show_valued_columns(self):
        """Whether the plain valued columns belong on this picking's slip.

        A more specific layout - the retail reception note - replaces the
        valued money columns (unit price, additional charges, subtotal, taxes,
        total) with its own cost/markup/shelf-price columns and turns this off,
        so the two do not both print and leave the table with two sets of money
        columns. Base behaviour is to show them; the retail picking report
        overrides this."""
        self.ensure_one()
        return True

    def _get_report_lang(self):
        """Print the stock documents of a Romanian company in Romanian.

        The delivery slip (NIR, aviz, bon de consum) is rendered in the
        partner's language, so a receipt from a foreign vendor, or a
        partnerless internal transfer or consume voucher, comes out in English.
        For a Romanian company these are legal documents that must read
        Romanian. ``ir.actions.report`` flags the render of this one report with
        ``l10n_ro_force_picking_report_lang``; we honour the flag here so every
        other report, and every non-RO company, keeps the partner's language.
        The Romanian language has to be installed, otherwise rendering with it
        raises ``Invalid language code`` - a RO company without it keeps the
        partner's language rather than crashing the slip."""
        lang = super()._get_report_lang()
        if (
            self.env.context.get("l10n_ro_force_picking_report_lang")
            and self.company_id.country_id.code == "RO"
            and any(
                code == "ro_RO" for code, _name in self.env["res.lang"].get_installed()
            )
        ):
            return "ro_RO"
        return lang

    def _compute_l10n_ro_is_internal(self):
        for pick in self:
            pick.l10n_ro_is_internal = pick.move_ids and not (
                pick.move_ids.mapped("sale_line_id")
                or pick.move_ids.mapped("purchase_line_id")
            )

    @api.depends(
        "state",
        "move_line_ids",
        "move_line_ids.quantity",
        "move_line_ids.l10n_ro_price_subtotal",
        "move_line_ids.l10n_ro_price_total",
    )
    def _compute_l10n_ro_valued_fields(self):
        for pick in self:
            pick.l10n_ro_currency_id = (
                pick.move_line_ids[0].l10n_ro_currency_id
                if pick.move_line_ids
                else pick.company_id.currency_id
            )
            pick.l10n_ro_amount_untaxed = 0
            pick.l10n_ro_amount_tax = 0
            pick.l10n_ro_amount_total = 0
            for line in pick.move_line_ids:
                pick.l10n_ro_amount_untaxed += line.l10n_ro_price_subtotal
                pick.l10n_ro_amount_tax += line.l10n_ro_price_tax
                pick.l10n_ro_amount_total += line.l10n_ro_price_total
