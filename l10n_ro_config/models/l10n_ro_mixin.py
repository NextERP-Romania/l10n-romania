# Copyright 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class L10nRoMixin(models.AbstractModel):
    _name = "l10n.ro.mixin"
    _description = "Mixin model for applying to any object that use Romanian Accounting"

    is_l10n_ro_record = fields.Boolean(
        string="Is Romanian Record",
        compute="_compute_is_l10n_ro_record",
        readonly=False,
    )

    @api.depends(lambda self: self._check_company_id_in_fields())
    @api.depends_context("company")
    def _compute_is_l10n_ro_record(self):
        for obj in self:
            has_company = obj._check_company_id_in_fields()
            has_company = has_company and obj.company_id
            company = obj.company_id if has_company else obj.env.company
            obj.is_l10n_ro_record = company._check_is_l10n_ro_record()

    def _check_company_id_in_fields(self):
        has_company = "company_id" in self.env[self._name]._fields
        if has_company:
            return ["company_id"]
        return []
