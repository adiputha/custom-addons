from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CashDenominationWizard(models.TransientModel):
    _name = 'cash.denomination.wizard'
    _description = 'Cash Denomination Wizard'

    request_id = fields.Many2one(
        'petty.cash.request',
        string='Petty Cash Request',
        readonly=True,
    )
    
    iou_request_id = fields.Many2one(
        'petty.cash.iou.request',
        string='IOU Request',
        readonly=True,
    )
    
    request_number = fields.Char(
        string='Request Number',
        readonly=True,
    )
    
    requested_amount = fields.Float(
        string='Request Amount',
        readonly=True,
    )
    
    request_type = fields.Selection([
        ('petty_cash', 'Petty Cash'),
        ('iou', 'IOU')
    ], string='Request Type', readonly=True)
    
    selected_amount = fields.Float(
        string='Selected Amount',
        compute='_compute_selected_amount',
        store=True,
    )
    
    cash_in_hand = fields.Float(
        string='Cash in Hand',
        default=15000.00, #needs to be dynamic based on actual cash in hand come from petty cash float
        readonly=True,
    )
    
    is_cash_balanced = fields.Boolean(
        string='Is Cash Balanced',
        default=False,
    )
    
    balance_amount = fields.Float(
        string='Balance Amount',
        compute='_compute_balance_amount',
        store=True,
    )
    
    # Denomination fields
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
    
    # Available denomination quantities (in hand)
    denom_5000_available = fields.Integer(string='Rs. 5,000 Available', default=2, readonly=True)
    denom_1000_available = fields.Integer(string='Rs. 1,000 Available', default=5, readonly=True)
    denom_500_available = fields.Integer(string='Rs. 500 Available', default=4, readonly=True)
    denom_100_available = fields.Integer(string='Rs. 100 Available', default=10, readonly=True)
    denom_50_available = fields.Integer(string='Rs. 50 Available', default=8, readonly=True)
    denom_20_available = fields.Integer(string='Rs. 20 Available', default=10, readonly=True)
    denom_10_available = fields.Integer(string='Rs. 10 Available', default=10, readonly=True)
    denom_5_available = fields.Integer(string='Rs. 5 Available', default=10, readonly=True)
    denom_2_available = fields.Integer(string='Rs. 2 Available', default=10, readonly=True)
    denom_1_available = fields.Integer(string='Rs. 1 Available', default=10, readonly=True)
    
    # Balance denomination fields (shown when is_cash_balanced is True)
    balance_5000_qty = fields.Integer(string='Balance Rs. 5,000', default=0)
    balance_1000_qty = fields.Integer(string='Balance Rs. 1,000', default=0)
    balance_500_qty = fields.Integer(string='Balance Rs. 500', default=0)
    balance_100_qty = fields.Integer(string='Balance Rs. 100', default=0)
    balance_50_qty = fields.Integer(string='Balance Rs. 50', default=0)
    balance_20_qty = fields.Integer(string='Balance Rs. 20', default=0)
    balance_10_qty = fields.Integer(string='Balance Rs. 10', default=0)
    balance_5_qty = fields.Integer(string='Balance Rs. 5', default=0)
    balance_2_qty = fields.Integer(string='Balance Rs. 2', default=0)
    balance_1_qty = fields.Integer(string='Balance Rs. 1', default=0)
    
    selected_balance_amount = fields.Float(
        string='Selected Balance Amount',
        compute='_compute_selected_balance_amount',
        store=True,
    )
    
    
    @api.depends('request_id')
    def _compute_request_details(self):
        for record in self:
            if record.request_id:
                record.request_number = record.request_id.name
                record.requested_amount = record.request_id.request_amount
            elif record.iou_request_id:
                record.request_number = record.iou_request_id.name
                record.requested_amount = record.iou_request_id.request_amount
            else:
                record.request_number = ''
                record.requested_amount = 0.0
    
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
    
        if self.env.context.get('default_request_id'):
            request_id = self.env.context.get('default_request_id')
           
            defaults['request_id'] = request_id
            #   defaults['request_type'] = 'petty_cash'
            
            request = self.env['petty.cash.request'].browse(request_id)
            if request.exists():
                defaults['request_number'] = request.name
                defaults['requested_amount'] = request.request_amount
        
        elif self.env.context.get('default_iou_request_id'):
            iou_request_id = self.env.context.get('default_iou_request_id')

            defaults['iou_request_id'] = iou_request_id
            #defaults['request_type'] = 'iou'
            
            iou_request = self.env['petty.cash.iou.request'].browse(iou_request_id)
            if iou_request.exists():
                defaults['request_number'] = iou_request.name
                defaults['requested_amount'] = iou_request.request_amount
                
        return defaults
    
    @api.depends('denom_5000_qty', 'denom_1000_qty', 'denom_500_qty', 'denom_100_qty',
                 'denom_50_qty', 'denom_20_qty', 'denom_10_qty', 'denom_5_qty',
                 'denom_2_qty', 'denom_1_qty')
    def _compute_selected_amount(self):
        for record in self:
            amount = (record.denom_5000_qty * 5000 +
                      record.denom_1000_qty * 1000 +
                      record.denom_500_qty * 500 +
                      record.denom_100_qty * 100 +
                      record.denom_50_qty * 50 +
                      record.denom_20_qty * 20 +
                      record.denom_10_qty * 10 +
                      record.denom_5_qty * 5 +
                      record.denom_2_qty * 2 +
                      record.denom_1_qty * 1)
            record.selected_amount = amount
    
    @api.depends('selected_amount', 'requested_amount')
    def _compute_balance_amount(self):
        for record in self:
            record.balance_amount = record.requested_amount - record.selected_amount
    
    @api.depends('balance_5000_qty', 'balance_1000_qty', 'balance_500_qty', 'balance_100_qty',
                 'balance_50_qty', 'balance_20_qty', 'balance_10_qty', 'balance_5_qty',
                 'balance_2_qty', 'balance_1_qty')
    def _compute_selected_balance_amount(self):
        for record in self:
            amount = (record.balance_5000_qty * 5000 +
                      record.balance_1000_qty * 1000 +
                      record.balance_500_qty * 500 +
                      record.balance_100_qty * 100 +
                      record.balance_50_qty * 50 +
                      record.balance_20_qty * 20 +
                      record.balance_10_qty * 10 +
                      record.balance_5_qty * 5 +
                      record.balance_2_qty * 2 +
                      record.balance_1_qty * 1)
            record.selected_balance_amount = amount
            
    @api.constrains('denom_5000_qty', 'denom_1000_qty', 'denom_500_qty', 'denom_100_qty',
                    'denom_50_qty', 'denom_20_qty', 'denom_10_qty', 'denom_5_qty',
                    'denom_2_qty', 'denom_1_qty')
    def _check_available_denominations(self):
        for record in self:
            if record.denom_5000_qty > record.denom_5000_available:
                raise UserError(_('Not enough Rs. 5,000 notes available'))
            if record.denom_1000_qty > record.denom_1000_available:
                raise UserError(_('Not enough Rs. 1,000 notes available'))
            if record.denom_500_qty > record.denom_500_available:
                raise UserError(_('Not enough Rs. 500 notes available'))
            if record.denom_100_qty > record.denom_100_available:
                raise UserError(_('Not enough Rs. 100 notes available'))
            if record.denom_50_qty > record.denom_50_available:
                raise UserError(_('Not enough Rs. 50 notes available'))
            if record.denom_20_qty > record.denom_20_available:
                raise UserError(_('Not enough Rs. 20 notes available'))
            if record.denom_10_qty > record.denom_10_available:
                raise UserError(_('Not enough Rs. 10 notes available'))
            if record.denom_5_qty > record.denom_5_available:
                raise UserError(_('Not enough Rs. 5 notes available'))
            if record.denom_2_qty > record.denom_2_available:
                raise UserError(_('Not enough Rs. 2 notes available'))
            if record.denom_1_qty > record.denom_1_available:
                raise UserError(_('Not enough Rs. 1 notes available'))
            
    def action_update_amount(self):
        """ update the denomination and process the request """
        self.ensure_one()
        
        if self.is_cash_balanced:
            expected_amount = self.requested_amount + self.selected_balance_amount
            if abs(self.selected_amount - expected_amount) > 0.01:
                raise UserError(_('Selected amount does not match the expected amount.'))
        else:
            if abs(self.selected_amount -self.requested_amount) > 0.01:
                raise UserError(_('Selected amount does not match the requested amount.'))
        
        
        #log the denomination details
        denomination_details = f"""
        Cash Issued:
        Rs. 5,000 x {self.denom_5000_qty} = Rs. {self.denom_5000_qty * 5000}
        Rs. 1,000 x {self.denom_1000_qty} = Rs. {self.denom_1000_qty * 1000}
        Rs. 500 x {self.denom_500_qty} = Rs. {self.denom_500_qty * 500}
        Rs. 100 x {self.denom_100_qty} = Rs. {self.denom_100_qty * 100}
        Rs. 50 x {self.denom_50_qty} = Rs. {self.denom_50_qty * 50}
        Rs. 20 x {self.denom_20_qty} = Rs. {self.denom_20_qty * 20}
        Rs. 10 x {self.denom_10_qty} = Rs. {self.denom_10_qty * 10}
        Rs. 5 x {self.denom_5_qty} = Rs. {self.denom_5_qty * 5}
        Rs. 2 x {self.denom_2_qty} = Rs. {self.denom_2_qty * 2}
        Rs. 1 x {self.denom_1_qty} = Rs. {self.denom_1_qty * 1}
        Total: Rs. {self.selected_amount}
        """
        
        if self.is_cash_balanced:
            denomination_details += f"\nBalance Given: Rs. {self.selected_balance_amount}"
            
        if self.request_id:
            self.request_id.state = 'cash_issued'
            self.request_id.message_post(body=denomination_details)
        
        elif self.iou_request_id:
            self.iou_request_id.state = 'pending_bill_submission'
            self.iou_request_id.cashReceivedByEmployee = True
            self.iou_request_id.message_post(body=denomination_details)
        else:
            raise UserError(_('No request found to process the cash denomination.'))
        
        return {
            'type': 'ir.actions.act_window_close',
        }
        
    def action_cancel(self):
        """ Cancel the cash denomination wizard """
        return {
            'type': 'ir.actions.act_window_close',
        }
