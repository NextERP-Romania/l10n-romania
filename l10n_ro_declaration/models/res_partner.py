# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError
from odoo.tools import ormcache


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _map_anaf_country_code(self, country_code):
        country_code_map = {
            "RE": "FR",
            "GP": "FR",
            "MQ": "FR",
            "GF": "FR",
            "EL": "GR",
        }
        return country_code_map.get(country_code, country_code)

    @ormcache("self.env")
    def _get_anaf_europe_codes(self):
        europe = self.env.ref("base.europe", raise_if_not_found=False)
        if not europe:
            europe = self.env["res.country.group"].search(
                [("name", "=", "Europe")], limit=1
            )
        return europe.country_ids.mapped("code")

    @ormcache("self.vat, self.country_id")
    def _parse_anaf_vat_info(self):
        """Return tuple with split info (country_code, identifier_type and
        vat_number) from vat and country partner
        """
        self.ensure_one()
        country_code = identifier_type = vat_number = False
        if self.vat:
            vat_number = self.vat
            prefix = self._map_anaf_country_code(vat_number[:2].upper())
            if prefix in self._get_anaf_europe_codes():
                country_code = prefix
                identifier_type = "3"
            else:
                country_code = self._map_anaf_country_code(self.country_id.code) or ""
                if country_code in self._get_anaf_europe_codes():
                    identifier_type = "3"
                else:
                    identifier_type = "4"
            if country_code == "RO":
                if self.vat_subjected:
                    identifier_type = "1"
                else:
                    identifier_type = "2"

            vat_number = vat_number.replace(country_code, "")
        else:
            raise ValidationError(
                _("The partner %s doesn't have a VAT set.") % (self.name)
            )
        return country_code, identifier_type, vat_number
