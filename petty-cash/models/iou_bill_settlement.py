from odoo import models, fields, api, _
from datetime import datetime


class IouBillSettlement(models.Model):
    _name = 'iou.bill.settlement'
    _description = 'IOU Bill Settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    #_rec_name = 'name'  # Use 'name' as the display name in views
    _order = 'date desc'
    
    iou_request_id = fields.Many2one(
        'petty.cash.iou.request',
        string='IOU Request',
        required=True,
        ondelete='cascade',
    )
    
    date = fields.Datetime(
        string='Settlement Date',
        required=True,
        default=fields.Datetime.now,  
    )
    
    category = fields.Selection([
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('accommodation', 'Accommodation'),
        ('taxi', 'Taxi'),
        ('fuel', 'Fuel'),
        ('stationery', 'Stationery'),
        ('other', 'Other'),
    ], string='Category', required=True) # This field might be configurable in the future
    
    amount = fields.Float(
        string='Amount',
        required=True,
        
    )
    
    receipt = fields.Binary(
        string='Receipt',
        attachment=True,
    )
    
    receipt_filename = fields.Char(
        string='Receipt Filename',
        
    )
    
    remarks = fields.Text(
        string='Remarks',
    )
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending')
    
    action = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string='Action')
    
    @api.onchange('action')
    def onchange_action(self):
        """Update status based on action selected"""
        if self.action == 'approve':
            self.status = 'approved'
        elif self.action == 'reject':
            self.status = 'rejected'

            
    
    