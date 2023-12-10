# Copyright (C) 2022 Dorin Hongu <dhongu(@)gmail(.)com
# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_ro_edi_manual = fields.Boolean(
        string="E-Invoice Manual submission", default=True
    )

    l10n_ro_edi_residence = fields.Integer(string="Period of Residence", default=5)

    @api.model
    def _l10n_ro_get_anaf_efactura_messages(self):
        # method to be used in cron job to auto download e-invoices from ANAF
        ro_companies = self.search([]).filtered(lambda c: c.country_id.code == "RO" and c.l10n_ro_account_anaf_sync_id)
        for company in ro_companies:
            anaf_config = company.l10n_ro_account_anaf_sync_id
            params = {"zile": 10, "cif": company.partner_id.l10n_ro_vat_number}
            content, status_code = anaf_config._l10n_ro_einvoice_call(
                "/listaMesajeFactura", params, method="GET"
            )
            if status_code == 200:
                company_messages = content.get("mesaje").filtered(
                    lambda m: m.get("cif") == company.partner_id.l10n_ro_vat_number and m.get("tip") == "FACTURA PRIMITA"
                )
                for message in company_messages:
                    invoice = self.env["account.move"].search([("l10n_ro_edi_download", "=", message.get("id_solicitare"))])
                    if not invoice:
                        new_invoice = self.env["account.move"].with_context(default_move_type="in_invoice").create({
                            "l10n_ro_edi_download": message.get("id_solicitare"),
                            "l10n_ro_edi_transaction": message.get("id"),
                        })
                        new_invoice.l10n_ro_download_zip_anaf()
