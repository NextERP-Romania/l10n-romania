# Copyright (C) 2021 Dakai Soft SRL
# Copyright (C) 2021 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "l10n.ro.mixin"]


    def l10n_ro_fix_nondeductible_vat_lines(self):
        moves = self.env["account.move"]
        to_remove_lines = self.env["account.move.line"]
        for line in self.filtered(lambda l: l.company_id.l10n_ro_accounting):
            move = line.move_id
            company = line.company_id
            tax_rep_line = line.tax_repartition_line_id
            # Remove the lines marked to be removed from stock non deductible
            if (
                line.display_type == "tax"
                and move.stock_move_id.l10n_ro_nondeductible_tax_id
                and tax_rep_line.l10n_ro_exclude_from_stock
            ):
                moves |= line.move_id
                to_remove_lines |= line
        to_remove_lines.with_context(dynamic_unlink=True).sudo().unlink()
        moves._sync_dynamic_lines(container={"records": moves, "self": moves})
        return to_remove_lines

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        to_remove_lines = lines.l10n_ro_fix_nondeductible_vat_lines()
        return lines - to_remove_lines
    
    def _convert_to_tax_line_dict(self):
        res = super()._convert_to_tax_line_dict()
        if res.get('tax_repartition_line_id') and res.get('tax_repartition_line_id').l10n_ro_nondeductible and self.acount_id.l10n_ro_nondeductible_account_id:
            res['account_id'] = self.acount_id.l10n_ro_nondeductible_account_id
        return res