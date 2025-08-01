from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class InitialDenominationWizard(models.TransientModel):
    _name = 'initial.denomination.wizard'
    _description = 'Initial Denomination Wizard'

    float_request_id = fields.Many2one(
        'float.request',
        string='Float Request',
        required=True,
        help="The float request for which initial denominations are being set."
    )

    float_name = fields.Char(
        related='float_request_id.name',
        string='Float Name',
        readonly=True,
        help="The name of the float request."
    )
    
    initial_amount = fields.Float(
        string='Initial Amount',
        related='float_request_id.initial_amount',
        readonly=True,
    )
    
    # Denomination fields
    denom_5000_qty = fields.Integer(string='Rs. 5,000 Notes', default=0)
    denom_1000_qty = fields.Integer(string='Rs. 1,000 Notes', default=0)
    denom_500_qty = fields.Integer(string='Rs. 500 Notes', default=0)
    denom_100_qty = fields.Integer(string='Rs. 100 Notes', default=0)
    denom_50_qty = fields.Integer(string='Rs. 50 Notes', default=0)
    denom_20_qty = fields.Integer(string='Rs. 20 Notes', default=0)
    denom_10_qty = fields.Integer(string='Rs. 10 Coins', default=0)
    denom_5_qty = fields.Integer(string='Rs. 5 Coins', default=0)
    denom_2_qty = fields.Integer(string='Rs. 2 Coins', default=0)
    denom_1_qty = fields.Integer(string='Rs. 1 Coins', default=0)
    
    calculated_total = fields.Float(
        string='Calculated Total',
        compute='_compute_calculated_total',
        store=True,
        help="Total amount calculated from the denominations."
    )
    
    difference = fields.Float(
        string='Difference',
        compute='_compute_difference',
        store=True,
    )
    
    is_balanced = fields.Boolean(
        string='Is Balanced',
        compute='_compute_is_balanced',
        help="Indicates if the total denominations match the float request's initial amount."
    )
    
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        
        float_request_id = (
            self.env.context.get('default_float_request_id') or
            self.env.context.get('active_id') or
            self.env.context.get('float_request_id')
        )
        
        if float_request_id:
            float_request = self.env['float.request'].browse(float_request_id)
            
            if float_request.exist():
                defaults['float_request_id'] = float_request.id
                
                suggested = self._suggest_denomination_breakdown(float_request.initial_amount)
                defaults.update(suggested)
        
        return defaults
    
    def _suggest_denomination_breakdown(self, amount):
        """Suggest a breakdown of denominations for the given amount."""
        remaining  = amount
        breakdown = {}
        
        denominations = [
            (5000, 'denom_5000_qty', 10),  # (value, field_name, max_notes)
            (1000, 'denom_1000_qty', 20),
            (500, 'denom_500_qty', 15),
            (100, 'denom_100_qty', 30),
            (50, 'denom_50_qty', 10),
            (20, 'denom_20_qty', 25),
            (10, 'denom_10_qty', 50),
            (5, 'denom_5_qty', 50),
            (2, 'denom_2_qty', 50),
            (1, 'denom_1_qty', 100),
        ]
        
        for value, field_name, max_notes in denominations:
            if remaining <= 0:
                breakdown[field_name] = 0
                continue
                
            # Calculate optimal quantity for this denomination
            needed = min(int(remaining / value), max_notes)
            breakdown[field_name] = needed
            remaining -= needed * value
        
        return breakdown
    
    @api.depends('denom_5000_qty', 'denom_1000_qty', 'denom_500_qty',
                 'denom_100_qty', 'denom_50_qty', 'denom_20_qty',
                 'denom_10_qty', 'denom_5_qty', 'denom_2_qty', 'denom_1_qty')
    def _compute_calculated_total(self):
        for record in self:
            record.calculated_total = (
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
            
    @api.depends('calculated_total', 'initial_amount')
    def _compute_difference(self):
        for record in self:
            record.difference = record.calculated_total - record.initial_amount
    
    @api.depends('difference')
    def _compute_is_balanced(self):
        for record in self:
            record.is_balanced = abs(record.difference) < 0.01
            
    @api.constrains('denom_5000_qty', 'denom_1000_qty', 'denom_500_qty', 'denom_100_qty',
                    'denom_50_qty', 'denom_20_qty', 'denom_10_qty', 'denom_5_qty',
                    'denom_2_qty', 'denom_1_qty')
    def _check_negative_values(self):
        for record in self:
            denomination_fields = [
                'denom_5000_qty', 'denom_1000_qty', 'denom_500_qty', 'denom_100_qty',
                'denom_50_qty', 'denom_20_qty', 'denom_10_qty', 'denom_5_qty',
                'denom_2_qty', 'denom_1_qty'
            ]
            
            for field in denomination_fields:
                if getattr(record, field) < 0:
                    raise ValidationError(_('Denomination quantities cannot be negative.'))
    
    def action_auto_calculate(self):
        """Auto-calculate optimal denomination breakdown"""
        self.ensure_one()
        suggested = self._suggest_denomination_breakdown(self.initial_amount)
        
        # Update the record with suggested values
        for field_name, value in suggested.items():
            setattr(self, field_name, value)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-calculated'),
                'message': _('Denomination breakdown has been automatically calculated.'),
                'type': 'success',
            }
        }
    
    def action_create_denomination(self):
        """Create the initial denomination record"""
        self.ensure_one()
        
        # Validate that total matches
        if not self.is_balanced:
            raise UserError(
                _('Total amount (Rs. %.2f) does not match float amount (Rs. %.2f). '
                  'Difference: Rs. %.2f') % 
                (self.calculated_total, self.initial_amount, self.difference)
            )
        
        # Check if denomination record already exists
        existing_denomination = self.env['float.denomination'].search([
            ('float_request_id', '=', self.float_request_id.id)
        ])
        
        if existing_denomination:
            raise UserError(_('Initial denomination record already exists for this float.'))
        
        # Create the denomination record
        denomination_data = {
            'float_request_id': self.float_request_id.id,
            'denom_5000_qty': self.denom_5000_qty,
            'denom_1000_qty': self.denom_1000_qty,
            'denom_500_qty': self.denom_500_qty,
            'denom_100_qty': self.denom_100_qty,
            'denom_50_qty': self.denom_50_qty,
            'denom_20_qty': self.denom_20_qty,
            'denom_10_qty': self.denom_10_qty,
            'denom_5_qty': self.denom_5_qty,
            'denom_2_qty': self.denom_2_qty,
            'denom_1_qty': self.denom_1_qty,
        }
        
        denomination_record = self.env['float.denomination'].create(denomination_data)
        
        # Log message on float request
        message = self._create_denomination_message()
        self.float_request_id.message_post(body=message)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Initial denomination record created successfully.'),
                'type': 'success',
            }
        }
    
    def _create_denomination_message(self):
        """Create a message showing the denomination breakdown"""
        message = f"""
        <h4>Initial Denomination Setup:</h4>
        <table class="table table-sm">
            <tr><td>Rs. 5,000 Notes:</td><td>{self.denom_5000_qty}</td><td>= Rs. {self.denom_5000_qty * 5000:,.2f}</td></tr>
            <tr><td>Rs. 1,000 Notes:</td><td>{self.denom_1000_qty}</td><td>= Rs. {self.denom_1000_qty * 1000:,.2f}</td></tr>
            <tr><td>Rs. 500 Notes:</td><td>{self.denom_500_qty}</td><td>= Rs. {self.denom_500_qty * 500:,.2f}</td></tr>
            <tr><td>Rs. 100 Notes:</td><td>{self.denom_100_qty}</td><td>= Rs. {self.denom_100_qty * 100:,.2f}</td></tr>
            <tr><td>Rs. 50 Notes:</td><td>{self.denom_50_qty}</td><td>= Rs. {self.denom_50_qty * 50:,.2f}</td></tr>
            <tr><td>Rs. 20 Notes:</td><td>{self.denom_20_qty}</td><td>= Rs. {self.denom_20_qty * 20:,.2f}</td></tr>
            <tr><td>Rs. 10 Coins:</td><td>{self.denom_10_qty}</td><td>= Rs. {self.denom_10_qty * 10:,.2f}</td></tr>
            <tr><td>Rs. 5 Coins:</td><td>{self.denom_5_qty}</td><td>= Rs. {self.denom_5_qty * 5:,.2f}</td></tr>
            <tr><td>Rs. 2 Coins:</td><td>{self.denom_2_qty}</td><td>= Rs. {self.denom_2_qty * 2:,.2f}</td></tr>
            <tr><td>Rs. 1 Coins:</td><td>{self.denom_1_qty}</td><td>= Rs. {self.denom_1_qty * 1:,.2f}</td></tr>
            <tr><td><strong>Total:</strong></td><td></td><td><strong>Rs. {self.calculated_total:,.2f}</strong></td></tr>
        </table>
        """
        return message
    
    def action_cancel(self):
        """Cancel the wizard"""
        return {'type': 'ir.actions.act_window_close'}