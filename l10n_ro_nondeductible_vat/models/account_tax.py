# Copyright (C) 2021 Dakai Soft SRL
# Copyright (C) 2021 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountTaxExtend(models.Model):
    _name = "account.tax"
    _inherit = ["account.tax", "l10n.ro.mixin"]

    l10n_ro_nondeductible_tax_id = fields.Many2one(
        "account.tax", copy=False, string="Romania - Nondeductible Tax"
    )
    l10n_ro_is_nondeductible = fields.Boolean(
        string="Romania - Is Nondeductible",
        compute="_compute_boolean_l10n_ro_nondeductible",
        store=True,
    )

    @api.depends("invoice_repartition_line_ids", "refund_repartition_line_ids")
    def _compute_boolean_l10n_ro_nondeductible(self):
        for record in self:
            if record.is_l10n_ro_record:
                record.l10n_ro_is_nondeductible = any(
                    record.invoice_repartition_line_ids.mapped("l10n_ro_nondeductible")
                    + record.refund_repartition_line_ids.mapped("l10n_ro_nondeductible")
                )
            else:
                record.l10n_ro_is_nondeductible = False
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False, handle_price_include=True, include_caba_tags=False, fixed_multiplicator=1):
        tax_vals_list = super().compute_all(
            price_unit, currency=currency, quantity=quantity, product=product, partner=partner,
            is_refund=is_refund, handle_price_include=handle_price_include,
            include_caba_tags=include_caba_tags, fixed_multiplicator=fixed_multiplicator
        )
        taxes = tax_vals_list.get('taxes')
        for tax_vals in taxes:
            if tax_vals.get('tax_repartition_line_id'):
                tax_repartition_line = self.env["account.tax.repartition.line"].browse(tax_vals['tax_repartition_line_id'])
                line_account = self.env['account.account'].browse(tax_vals['account_id'])
                company = tax_repartition_line.company_id
                if tax_repartition_line.l10n_ro_nondeductible and not tax_repartition_line.account_id:
                    # if company.l10n_ro_nondeductible_account_id:
                    #     tax_vals['account_id'] = company.l10n_ro_nondeductible_account_id.id
                    if line_account.l10n_ro_nondeductible_account_id:
                        tax_vals['account_id'] = line_account.l10n_ro_nondeductible_account_id.id
        return tax_vals_list

    @api.model
    def _get_generation_dict_from_base_line(self, line_vals, tax_vals, force_caba_exigibility=False):
        res = super()._get_generation_dict_from_base_line(line_vals, tax_vals, force_caba_exigibility=force_caba_exigibility)
        if tax_vals.get('tax_repartition_line_id'):
            tax_repartition_line = self.env["account.tax.repartition.line"].browse(tax_vals['tax_repartition_line_id'])
            line_account = self.env['account.account'].browse(line_vals['account_id'])
            company = tax_repartition_line.company_id
            if tax_repartition_line.l10n_ro_nondeductible and not tax_repartition_line.account_id:
                # if company.l10n_ro_nondeductible_account_id:
                #     res['account_id'] = company.l10n_ro_nondeductible_account_id.id
                if line_account.l10n_ro_nondeductible_account_id:
                    res['account_id'] = line_account.l10n_ro_nondeductible_account_id.id
        return res
    
    @api.model
    def _compute_taxes_for_single_line(self, base_line, handle_price_include=True, include_caba_tags=False, early_pay_discount_computation=None, early_pay_discount_percentage=None):
        to_update_vals, tax_values_list = super()._compute_taxes_for_single_line(base_line, handle_price_include=handle_price_include, include_caba_tags=include_caba_tags, early_pay_discount_computation=early_pay_discount_computation, early_pay_discount_percentage=early_pay_discount_percentage)
        for tax_vals in tax_values_list:
            if tax_vals.get('tax_repartition_line_id'):
                tax_repartition_line = self.env["account.tax.repartition.line"].browse(tax_vals['tax_repartition_line_id'])
                if tax_repartition_line.l10n_ro_nondeductible and not tax_repartition_line.account_id:
                    if base_line['account'].l10n_ro_nondeductible_account_id:
                        tax_vals['account_id'] = base_line['account'].l10n_ro_nondeductible_account_id.id
        return to_update_vals, tax_values_list