# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

import requests

from odoo import api, fields, models


from odoo.addons.l10n_ro_partner_create_by_vat.models import res_partner

res_partner.AnafFiled_OdooField_Overwrite.extend([
    ("anaf_data", "data", "over_all_the_time"),
    ("act", "act", "over_all_the_time"),
    ("stare_inregistrare", "stare_inregistrare", "over_all_the_time"),
    ("scpTVA", "scpTVA", "over_all_the_time"),
    ("data_inceput_ScpTVA", "data_inceput_ScpTVA", "over_all_the_time"),
    ("data_sfarsit_ScpTVA", "data_sfarsit_ScpTVA", "over_all_the_time"),
    ("data_anul_imp_ScpTVA", "data_anul_imp_ScpTVA", "over_all_the_time"),
    ("mesaj_ScpTVA", "mesaj_ScpTVA", "over_all_the_time"),
    ("dataInceputTvaInc", "dataInceputTvaInc", "over_all_the_time"),
    ("dataSfarsitTvaInc", "dataSfarsitTvaInc", "over_all_the_time"),
    ("dataActualizareTvaInc", "dataActualizareTvaInc", "over_all_the_time"),
    ("dataPublicareTvaInc", "dataPublicareTvaInc", "over_all_the_time"),
    ("tipActTvaInc", "tipActTvaInc", "over_all_the_time"),
    ("statusTvaIncasare", "statusTvaIncasare", "over_all_the_time"),
    ("dataInactivare", "dataInactivare", "over_all_the_time"),
    ("dataReactivare", "dataReactivare", "over_all_the_time"),
    ("dataPublicare", "dataPublicare", "over_all_the_time"),
    ("dataRadiere", "dataRadiere", "over_all_the_time"),
    ("statusInactivi", "statusInactivi", "over_all_the_time"),
    ("dataInceputSplitTVA", "dataInceputSplitTVA", "over_all_the_time"),
    ("dataAnulareSplitTVA", "dataAnulareSplitTVA", "over_all_the_time"),
    ("statusSplitTVA", "statusSplitTVA", "over_all_the_time"),
    ("iban", "iban", "over_all_the_time"),
    ("statusRO_e_Factura", "statusRO_e_Factura", "over_all_the_time"),
    ])

_logger = logging.getLogger(__name__)



class ResPartner(models.Model):
    _inherit = "res.partner"

    country_name = fields.Char(related="country_id.name") # just for a xml domain

    anaf_data = fields.Date(help="The date when following anaf data is taken",)
    act = fields.Char("Act autorizare",)
    stare_inregistrare = fields.Char("Stare Societate",)
    scpTVA = fields.Boolean( help="true -pentru platitor in scopuri de tva / false in cazul in care nu"
        "e platitor  in scopuri de TVA la data cautata""",)
    data_inceput_ScpTVA = fields.Date(help="Data înregistrării în scopuri de TVA anterioară",)
    data_sfarsit_ScpTVA = fields.Date(help="Data anulării înregistrării în scopuri de TVA",)
    data_anul_imp_ScpTVA = fields.Date(help="Data operarii anularii înregistrării în scopuri de TVA",)
    mesaj_ScpTVA = fields.Char(help="MESAJ:(ne)platitor de TVA la data cautata",)
    dataInceputTvaInc = fields.Date( help= "Data de la care aplică sistemul TVA la încasare",)
    dataSfarsitTvaInc = fields.Date(help="Data până la care aplică sistemul TVA la încasare",)
    dataActualizareTvaInc = fields.Date(help="Data actualizarii tva incasare",)
    dataPublicareTvaInc = fields.Date(help="Data publicarii tva incasare",)
    tipActTvaInc = fields.Char(help="Tip actualizare  tva incasare  'Radiere'",)
    statusTvaIncasare = fields.Char(help="true -pentru platitor TVA la incasare/ false in"
            " cazul in care nu e platitor de TVA la incasare la data cautata",)
    dataInactivare = fields.Date()
    dataReactivare = fields.Date()
    dataPublicare = fields.Date()
    dataRadiere = fields.Date()
    statusInactivi =fields.Boolean(help=" true -pentru inactiv / false"
        " in cazul in care nu este inactiv la data cautata")
    dataInceputSplitTVA = fields.Date()
    dataAnulareSplitTVA = fields.Date()
    statusSplitTVA = fields.Boolean(help="true -aplica plata defalcata"
        " a Tva / false - nu aplica plata defalcata a Tva la data cautata")
    iban = fields.Char(help="contul IBAN taken from anaf")
    statusRO_e_Factura = fields.Boolean(help= "true - figureaza in"
        " Registrul RO e-Factura / false - nu figureaza in Registrul RO e-Factura "
        "la data cautata")
    
    def refresh_anaf_data(self):
        self.ro_vat_change()

 