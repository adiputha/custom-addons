from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FloatDenomination(models.Model):
    _name = 'float.denomination'
    _description = 'Float Denomination'
    _order = 'float_request_id'
    
    float_request_id = fields.Many2one(
        'float.request',
        string='Float Request',
        required=True,
        ondelete='cascade',
        help="The float request associated with this denomination."
    )
    
    # Denomination quantities
    denom_5000_qty = fields.Integer(string='Rs. 5,000 Quantity', default=0)
    denom_1000_qty = fields.Integer(string='Rs. 1,000 Quantity', default=0)
    denom_500_qty = fields.Integer(string='Rs. 500 Quantity', default=0)
    denom_100_qty = fields.Integer(string='Rs. 100 Quantity', default=0)
    denom_50_qty = fields.Integer(string='Rs. 50 Quantity', default=0)
    denom_20_qty = fields.Integer(string='Rs. 20 Quantity', default=0)
    denom_10_qty = fields.Integer(string='Rs. 10 Quantity', default=0)
    denom_5_qty = fields.Integer(string='Rs. 5 Quantity', default=0)
    denom_2_qty = fields.Integer(string='Rs. 2 Quantity', default=0)
    denom_1_qty = fields.Integer(string='Rs. 1 Quantity', default=0)
    
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
        help="Total amount calculated from the denominations."
    )
    
    last_updated = fields.Datetime(
        string='Last Updated',
        default=fields.Datetime.now,    
    )
    
    @api.depends('denom_5000_qty', 'denom_1000_qty', 'denom_500_qty',
                 'denom_100_qty', 'denom_50_qty', 'denom_20_qty',
                 'denom_10_qty', 'denom_5_qty', 'denom_2_qty', 'denom_1_qty')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = (
                (record.denom_5000_qty * 5000) +
                (record.denom_1000_qty * 1000) +
                (record.denom_500_qty * 500) +
                (record.denom_100_qty * 100) +
                (record.denom_50_qty * 50) +
                (record.denom_20_qty * 20) +
                (record.denom_10_qty * 10) +
                (record.denom_5_qty * 5) +
                (record.denom_2_qty * 2) +
                (record.denom_1_qty * 1)
            )
            
    def update_denomination_after_reimbursement(self, denomination_used):
        """Update the float request's current amount after reimbursement."""
        self.ensure_one()
        
        self.denom_5000_qty -= denomination_used.get('denom_5000_qty', 0)
        self.denom_1000_qty -= denomination_used.get('denom_1000_qty', 0)
        self.denom_500_qty -= denomination_used.get('denom_500_qty', 0)
        self.denom_100_qty -= denomination_used.get('denom_100_qty', 0)
        self.denom_50_qty -= denomination_used.get('denom_50_qty', 0)
        self.denom_20_qty -= denomination_used.get('denom_20_qty', 0)
        self.denom_10_qty -= denomination_used.get('denom_10_qty', 0)
        self.denom_5_qty -= denomination_used.get('denom_5_qty', 0)
        self.denom_2_qty -= denomination_used.get('denom_2_qty', 0)
        self.denom_1_qty -= denomination_used.get('denom_1_qty', 0)
        
        self.last_updated = fields.Datetime.now()
        
    def add_denomination_from_reimbursement(self, denomination_used):
        """Add denominations back to the float request after reimbursement."""
        self.ensure_one()
        
        self.denom_5000_qty += denomination_used.get('denom_5000_qty', 0)
        self.denom_1000_qty += denomination_used.get('denom_1000_qty', 0)
        self.denom_500_qty += denomination_used.get('denom_500_qty', 0)
        self.denom_100_qty += denomination_used.get('denom_100_qty', 0)
        self.denom_50_qty += denomination_used.get('denom_50_qty', 0)
        self.denom_20_qty += denomination_used.get('denom_20_qty', 0)
        self.denom_10_qty += denomination_used.get('denom_10_qty', 0)
        self.denom_5_qty += denomination_used.get('denom_5_qty', 0)
        self.denom_2_qty += denomination_used.get('denom_2_qty', 0)
        self.denom_1_qty += denomination_used.get('denom_1_qty', 0)
        
        self.last_updated = fields.Datetime.now()
            