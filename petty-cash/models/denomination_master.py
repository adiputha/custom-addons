from odoo import models, fields, api, _
from datetime import date

class DenominationMaster(models.Model):
    _name = "petty.cash.denomination.master"
    _description = "Denomination Master"
    _rec_name = "name"

    name = fields.Char(
        string="Denomination Name", 
        required=True)

    value = fields.Float(
        string="Value", 
        required=True)
    
    currency_id = fields.Many2one(
        "res.currency", 
        string="Currency", 
        required=True)
    
    active = fields.Boolean(
        string="Active", 
        default=True)

