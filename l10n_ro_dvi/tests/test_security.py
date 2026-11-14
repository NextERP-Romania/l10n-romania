# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDviAccess(TransactionCase):
    def test_internal_user_cannot_access_landed_costs(self):
        user = self.env["res.users"].create(
            {
                "name": "Non-accounting internal user",
                "login": "non-accounting-internal",
                "group_ids": [Command.set([self.env.ref("base.group_user").id])],
            }
        )

        with self.assertRaises(AccessError):
            self.env["stock.landed.cost"].with_user(user).check_access("read")
