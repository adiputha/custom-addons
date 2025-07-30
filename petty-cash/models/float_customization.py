from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class FloatCustomization(models.Model):
    _name = 'float.customization'
    _description = 'Float Customization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'float_request_id'
    
    float_request_id = fields.Many2one(
        'float.request',
        string='Float',
        required= True,
        domain= [('state', '=' , 'approved')],
        tracking=True,
        help='Select the float to customize',
    )
    
    current_float_name = fields.Char(
        string='Current Float name',
        related='float_request_id.name',
        required=True,
    )
    
    current_department_id = fields.Many2one(
        'hr.department',
        string='Current Department',
        related='float_request_id.department_id',
        required=True,
    )

    current_initial_amount = fields.Float(
        string='Current Initial Amount',
        related='float_request_id.initial_amount',
        required=True,
    )
    
    current_can_exceed = fields.Boolean(
        string='Current Can Exceed',
        related='float_request_id.can_exceed',
        # readonly=True,
    )
    
    current_float_manager_id  = fields.Many2one(
        'res.users',
        string='Current Float Manager',
        related='float_request_id.float_manager_id',
        readonly=True,
    )
    
    #Modificaion Fields
    
    modify_float_amount = fields.Boolean(
        string='Modify Float Amount?',
        default= False,
        tracking=True,
        help='Check this to modify the float amount',
    )


    new_float_amount = fields.Float(
        string='New Float Amount',
        tracking=True,
        help='New initial amount for the float'
    )
    
    modify_can_exceed = fields.Boolean(
        string='Modify Exceed Permission?',
        default=False,
        tracking=True
    )
    
    new_can_exceed = fields.Boolean(
        string='New Can Exceed Setting',
        tracking=True,
        help='New setting for exceed permission'
    )
    
    new_exceed_limit = fields.Float(
        string='New Exceed Limit',
        help='New exceed limit amount'
    )
    
    modify_float_manager = fields.Boolean(
        string='Change Float Manager?',
        default=False,
        tracking=True
    )
    
    new_float_manager_id = fields.Many2one(
        'res.users',
        string='New Float Manager',
        tracking=True,
        help='New manager for this float'
    )
    
    reason_for_change = fields.Text(
        string='Reason for Change',
        required=True,
        tracking=True,
        help='Explain why these changes are needed'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)
    
    request_date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now,
        readonly=True
    )
    
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        tracking=True
    )
    
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True
    )
    
    remarks = fields.Text(
        string='Remarks',
        help='Additional comments'
    )
    
    @api.onchange('modify_float_amount')
    def _onchange_modify_float_amount(self):
        """Clear new float amount when unchecked"""
        if not self.modify_float_amount:
            self.new_float_amount = 0.0
            
    @api.onchange('modify_can_exceed')
    def _onchange_modify_can_exceed(self):
        """Clear exceed settings when unchecked"""
        if not self.modify_can_exceed:
            self.new_can_exceed = False
            self.new_exceed_limit = 0.0
            
    @api.constrains('new_float_amount', 'new_exceed_limit')
    def _check_amounts(self):
        """Validate amount fields"""
        for record in self:
            if record.modify_float_amount and record.new_float_amount <= 0:
               raise ValidationError(_('New float amount must be greater than zero.'))
            if record.modify_can_exceed and record.new_can_exceed and record.new_exceed_limit <= 0:
                raise ValidationError(_('New exceed limit must be greater than zero.'))
    
    @api.constrains('modify_float_amount', 'modify_can_exceed', 'modify_float_manager')
    def _check_modifications(self):
        """Ensure at least one modification is selected"""
        for record in self:
            if not any([record.modify_float_amount, record.modify_can_exceed, record.modify_float_manager]):
                raise ValidationError(_('Please select at least one modification to make.'))

    
    def action_submit(self):
        """Submit request for approval"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            record.state = 'requested'
            record.message_post(
                body=_('Float customization request submitted for approval.'),
                message_type='notification'
            )
            
    def action_approve(self):
        """Approve the customization request"""
        for record in self:
            if record.state != 'requested':
                raise UserError(_('Only requested customizations can be approved.'))
            
            float_record = record.float_request_id
            changes = []
            
            if record.modify_float_amount:
                old_amount = float_record.initial_amount
                float_record.initial_amount = record.new_float_amount
                changes.append(f'Float amount changed from {old_amount} to {record.new_float_amount}')
                
            if record.modify_can_exceed:
                old_can_exceed = float_record.can_exceed
                float_record.can_exceed = record.new_can_exceed
                if record.new_can_exceed:
                    float_record.exceed_limit = record.new_exceed_limit
                    changes.append(f'Exceed permission changed from {old_can_exceed} to {record.new_can_exceed} with limit Rs. {record.new_exceed_limit}')
                else:
                     changes.append(f'Exceed permission changed from {old_can_exceed} to {record.new_can_exceed}')
               
            if record.modify_float_manager:
                old_manager = float_record.float_manager_id.name
                float_record.float_manager_id = record.new_float_manager_id
                changes.append(f'Float manager changed from {old_manager} to {record.new_float_manager_id.name}')
            
            record.state = 'approved'
            record.approved_by = self.env.user
            record.approval_date = fields.Datetime.now()
            
            changes_summary = '\n'.join(changes)
            record.message_post(
                body=_('Float customization approved by %s:\n%s') % (self.env.user.name, changes_summary),
                message_type='notification'
            )
            
            float_record.message_post(
                body=_('Float customization approved: %s') % changes_summary,
                message_type='notification'
            )
            
    def action_reject(self):
        """Reject the customization request"""
        for record in self:
            if record.state != 'requested':
                raise UserError(_('Only requested customizations can be rejected.'))
            record.state = 'rejected'
            record.message_post(
                body=_('Float customization request rejected by %s') % self.env.user.name,
                message_type='notification'
            )
            
    def action_reset_to_draft(self):
        """Reset to draft state"""
        for record in self:
            if record.state not in ['rejected']:
                raise UserError(_('Only rejected requests can be reset to draft.'))
            record.state = 'draft'      
            
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            result.append((record.id, record.name))
        return result