from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PettyCashConfig(models.Model):
    _name = "petty.cash.config"
    _description = "Petty Cash Configuration"
    _rec_name = "name"
    
    name = fields.Char(
        string="Configuration Name",
        required=True,
        help="Name of the petty cash configuration.",
    )
    
    allow_cross_department_across = fields.Boolean(
        string="Allow Cross Department Across",
        default=False,
        help="Allow petty cash transactions across different departments.",
    )
    
    default_petty_cash_due_days = fields.Integer(
        string="Default Petty Cash Due Days",
        default=0,
        help="Default number of days before petty cash is due.",
    )
    
    default_iou_due_days = fields.Integer(
        string="Default IOU Due Days",
        default=10,
        help="Default number of days before IOU is due.",
    )
    
    
    
    