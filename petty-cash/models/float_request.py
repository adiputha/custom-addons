from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError


class FloatRequest(models.Model):
    _name = 'float.request'
    _description = 'Float Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    
    name = fields.Char(
        string='Float Name',
        required=True,
        tracking=True,
        help="Name of the float request."
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
        tracking=True,
        help='Department this float belongs to'
    )
    
    initial_amount = fields.Float(
        string='Initial Float Amount',
        required=True,
        tracking=True,
        help='Initial amount allocated for the float request.'
    )
    
    current_amount = fields.Float(
        string='Current Balance',
        compute='_compute_current_amount',
        store=True,
        help='Current balance of the float request.'
    )
    
    can_exceed = fields.Boolean(
        string='Can Exceed over the Initial Amount?',
        default=False,
        tracking=True,
    )
    
    exceed_limit = fields.Float(
        string='Exceed Limit',
        help='Limit for exceeding the initial amount if can_exceed is True.',
        default=0.0,
        tracking=True,
    )
    
    float_manager_id = fields.Many2one(
        'res.users',
        string='Float Manager',
        required=True,
        default=lambda self: self.env.user,
        help='User responsible for managing this float request.'
    )
    
    date_created = fields.Date(
        string='Date',
        readonly=True,
        default=fields.Date.today,
        tracking=True,
    )
    
    remarks = fields.Text(
        string='Remarks',
    )
    
    attachment = fields.Binary(
        string='Attachment',
        help='Attachment related to the float request.'
    )
    
    attachment_filename = fields.Char(
        string='Attachment Filename',
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    petty_cash_request_id = fields.One2many(
        'petty.cash.request',
        'float_request_id',
        string='Petty Cash Requests',
    )
    
    iou_request_id = fields.One2many(
        'petty.cash.iou.request',
        'float_request_id',
        string='IOU Requests',
    )

    total_iou_requests = fields.Integer(
        string= 'Total IOU Requests',
        compute='_compute_request_totals',
        store=True,
    )
    
    total_petty_cash_requests = fields.Integer(
        string= 'Total Petty Cash Requests',
        compute='_compute_request_totals',
        store=True,
    )
    
    total_requests = fields.Integer(
        string='Total Requests',
        compute='_compute_request_totals',
        store=True,
    )
    
    cash_in_hand = fields.Float(
        string='Cash in Hand',
        compute='_compute_cash_in_hand',
        store=True,
        help='Available cash for disbursement'
    )
    
    iou_amount = fields.Float(
        string = 'IOU Amount',
        compute='_compute_iou_amount',
        store=True,
        help='Total IOU amount requested against this float'
    )
    
    denomination_ids = fields.One2many(
        'float.denomination',
        'float_request_id',
        string='Denominations',
        help='Denominations used in this float request.'
    )
    
    current_denomination_id = fields.Many2one(
        'float.denomination',
        string='Current Denomination',
        help='Current denomination used for this float request.',
        compute='_compute_current_denomination',
        store=True
    )
    
    @api.depends('denomination_ids')
    def _compute_current_denomination(self):
        for record in self:
            if record.denomination_ids:
                record.current_denomination_id = record.denomination_ids.sorted('last_updated', reversed=True)[0]
            else:
                record.current_denomination_id = False
                
    def create_initial_denomination_record(self):
        """Create an initial denomination record for the float request."""
        self.ensure_one()
        if not self.denomination_ids and self.state == 'approved':
            
            intial_amount = self.initial_amount
            denom_data = self._calculate_initial_denominations(intial_amount)
            
            self.env['float.denomination'].create({
                'float_request_id': self.id,
                **denom_data
            })
            
    def _calculate_initial_denominations(self, amount):
        """Calculate the initial denominations based on the given amount."""
        
        remaining_amount = amount

        denom_5000 = min(int(remaining_amount / 5000), 10)  # Max 10 notes of 5000
        remaining_amount -= denom_5000 * 5000

        denom_1000 = min(int(remaining_amount / 1000), 20)  # Max 20 notes of 1000
        remaining_amount -= denom_1000 * 1000

        denom_500 = min(int(remaining_amount / 500), 20)
        remaining_amount -= denom_500 * 500

        denom_100 = min(int(remaining_amount / 100), 50)
        remaining_amount -= denom_100 * 100
        
        denom_50 = min(int(remaining_amount / 50), 20)
        remaining_amount -= denom_50 * 50
        
        denom_20 = min(int(remaining_amount / 20), 50)
        remaining_amount -= denom_20 * 20
        
        denom_10 = min(int(remaining_amount / 10), 100)
        remaining_amount -= denom_10 * 10
        
        denom_5 = min(int(remaining_amount / 5), 100)
        remaining_amount -= denom_5 * 5
        
        denom_2 = min(int(remaining_amount / 2), 100)
        remaining_amount -= denom_2 * 2
        
        denom_1 = int(remaining_amount)
    
        return {
            'denom_5000_qty': denom_5000,
            'denom_1000_qty': denom_1000,
            'denom_500_qty': denom_500,
            'denom_100_qty': denom_100,
            'denom_50_qty': denom_50,
            'denom_20_qty': denom_20,
            'denom_10_qty': denom_10,
            'denom_5_qty': denom_5,
            'denom_2_qty': denom_2,
            'denom_1_qty': denom_1,
        }
        
    def action_approve(self):
        """Override to create initial denomination record"""
        result = super().action_approve()
        for record in self:
            record.create_initial_denomination_record()
        return result
    
    def action_view_denominations(self):
        """Open the denomination records for this float"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Denominations - {self.name}',
            'res_model': 'float.denomination',
            'view_mode': 'list,form',
            'domain': [('float_request_id', '=', self.id)],
            'context': {
                'default_float_request_id': self.id,
            }
        }
    
    @api.depends('iou_request_id', 'petty_cash_request_id')
    def _compute_request_totals(self):
        for record in self:
            record.total_iou_requests = len(record.iou_request_id)
            record.total_petty_cash_requests = len(record.petty_cash_request_id)
            record.total_requests = record.total_iou_requests + record.total_petty_cash_requests

    @api.depends('initial_amount', 'petty_cash_request_id.request_amount', 'petty_cash_request_id.state')
    def _compute_current_amount(self):
        for record in self:
            completed_requests = record.petty_cash_request_id.filtered(
                lambda r: r.state in ['approved', 'completed', 'cash_issued']
            )
            disbursed_amount = sum(completed_requests.mapped('request_amount'))
            record.current_amount = record.initial_amount - disbursed_amount
            
    @api.depends('current_amount', 'iou_request_id.state', 'iou_request_id.request_amount')
    def _compute_cash_in_hand(self):
        for record in self:
            pending_ious = record.iou_request_id.filtered(
                lambda r: r.state in ['pending_bill_submission', 'cash_issued']
            )
            iou_amount = sum(pending_ious.mapped('request_amount'))
            record.cash_in_hand = record.current_amount - iou_amount
            
    @api.depends('iou_request_id.request_amount', 'iou_request_id.state')
    def _compute_iou_amount(self):
        for record in self:
            pending_ious = record.iou_request_id.filtered(
                lambda r: r.state in ['pending_bill_submission', 'cash_issued']
            )
            record.iou_amount = sum(pending_ious.mapped('request_amount'))
            
    @api.constrains('initial_amount', 'exceed_limit')
    def _check_amounts(self):
        for record in self:
            if record.initial_amount <= 0:
                raise ValidationError(_('Initial amount must be greater than zero.'))
            if record.can_exceed and record.exceed_limit <= 0:
                raise ValidationError(_('Exceed limit must be greater than zero when exceed is allowed.'))

    def action_submit(self):
        """Submit the float request for approval."""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            record.state = 'requested'
            record.message_post(
                body=_('Float request submitted for approval.'),
                message_type='notification',
            )
    
    def action_approve(self):
        """Approve the float request."""
        for record in self:
            if record.state != 'requested':
                raise UserError(_('Only requests in "Requested" state can be approved.'))
            record.state = 'approved'
            record.message_post(
                body=_('Float request approved by %s') % self.env.user.name,
                message_type='notification'
            )
                    
    
    def action_reject(self):
        """Reject the float request."""
        for record in self:
            if record.state != 'requested':
                raise UserError(_('Only requests in "Requested" state can be rejected.'))
            record.state = 'rejected'
            record.message_post(
                body=_('Float request rejected by %s') % self.env.user.name,
                message_type='notification'
            )
            
    def action_reset_to_draft(self):
        """Reset the float request to draft state."""
        for record in self:
            if record.state not in ['rejected', 'cancelled']:
                raise UserError(_('Only rejected or cancelled requests can be reset to draft.'))
            record.state = 'draft'
            
    def action_view_petty_cash_requests(self):
        """Open the related petty cash requests."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Petty Cash Requests - {self.name}',
            'res_model': 'petty.cash.request',
            'view_mode': 'list,form',
            'domain': [('float_request_id', '=', self.id)],
            'context': {
                'default_float_request_id': self.id,
                'default_request_type': 'petty_cash',
            }
        }
        
    def action_view_iou_requests(self):
        """Open the related IOU requests."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'IOU Requests - {self.name}',
            'res_model': 'petty.cash.iou.request',
            'view_mode': 'list,form',
            'domain': [('float_request_id', '=', self.id)],
            'context': {
                'default_float_request_id': self.id,
            }
        }