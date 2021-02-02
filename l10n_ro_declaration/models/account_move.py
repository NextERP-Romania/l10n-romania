# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

INVOICE_ORIGIN = [
    ("1", "facturi"),
    ("2", "borderouri"),
    ("3", "file carnet comercializare"),
    ("4", "contracte"),
    ("5", "alte documente"),
]

OPERATION_TYPE = [
    ("L", "Customer Invoice"),
    ("A", "Supplier Invoice"),
    ("LS", "Special Customer Invoice"),
    ("AS", "Special Supplier Invoice"),
    ("AI", "VAT on Payment Supplier Invoice"),
    ("V", "Inverse Taxation Customer Invoice"),
    ("C", "Inverse Taxation Supplier Invoice"),
    ("N", "Fizical Persons Supplier Invoice"),
]


class AccountMove(models.Model):
    _inherit = "account.move"

    correction = fields.Boolean("Correction Invoice")
    special_regim = fields.Boolean("Special Regime")

    # store partner data in case of some future partner modification
    # for reports to have the values form invoice time
    invoice_partner_display_vat = fields.Char(
        "VAT Number", compute="_compute_vat_store", store=True
    )
    invoice_origin_d394 = fields.Selection(
        INVOICE_ORIGIN, string="Document type", default="1"
    )
    partner_type = fields.Char(
        "D394 Partner Type", compute="_compute_partner_type", store=True
    )
    operation_type = fields.Selection(
        OPERATION_TYPE,
        compute="_compute_operation_type",
        string="Operation Type",
        store=True,
    )

    @api.depends("commercial_partner_id")
    def _compute_vat_store(self):
        for record in self:
            record.invoice_partner_display_vat = record.commercial_partner_id.vat or ""

    @api.depends("commercial_partner_id")
    def _compute_partner_type(self):
        for invoice in self:
            identifier_type = "1"
            if invoice.commercial_partner_id:
                (
                    country_code,
                    identifier_type,
                    vat_number,
                ) = invoice.commercial_partner_id._parse_anaf_vat_info()
            invoice.partner_type = identifier_type

    @api.depends(
        "partner_id",
        "partner_type",
        "move_type",
        "invoice_origin_d394",
        "fiscal_position_id",
    )
    def _compute_operation_type(self):
        fp = self.company_id.property_inverse_taxation_position_id
        if not fp:
            fp = self.env["account.fiscal.position"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("name", "=", "Regim Taxare Inversa"),
                ]
            )
        tva_fp = self.company_id.property_vat_on_payment_position_id
        if not tva_fp:
            tva_fp = self.env["account.fiscal.position"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("name", "=", "Regim TVA la Incasare"),
                ]
            )
        for inv in self:
            if inv.commercial_partner_id:
                (
                    country_code,
                    identifier_type,
                    vat_number,
                ) = inv.commercial_partner_id._parse_anaf_vat_info()
                if inv.move_type in ("out_invoice", "out_refund"):
                    if inv.fiscal_position_id == fp:
                        oper_type = "V"
                    elif identifier_type in ("1", "2") and inv.special_regim:
                        oper_type = "LS"
                    elif identifier_type in ("3", "4"):
                        oper_type = "V"
                    else:
                        oper_type = "L"
                else:
                    if inv.partner_type == "2" and inv.invoice_origin_d394:
                        oper_type = "N"
                    elif inv.partner_type in ("3", "4"):
                        oper_type = "C"
                    elif inv.fiscal_position_id == fp:
                        oper_type = "C"
                    elif inv.special_regim:
                        oper_type = "AS"
                    elif inv.fiscal_position_id == tva_fp:
                        oper_type = "AI"
                    else:
                        oper_type = "A"
                inv.operation_type = oper_type
        return True
