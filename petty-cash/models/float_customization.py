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
        readonly=True,
        store=True,
    )
    
    current_department_id = fields.Many2one(
        'hr.department',
        string='Current Department',
        related='float_request_id.department_id',
        readonly=True,
        store=True,
    )

    current_initial_amount = fields.Float(
        string='Current Initial Amount',
        related='float_request_id.initial_amount',
        readonly=True,
        store=True,
    )
    
    current_can_exceed = fields.Boolean(
        string='Current Can Exceed',
        related='float_request_id.can_exceed',
        # readonly=True,
        store=True,
    )

    current_exceed_limit = fields.Float(
        string='Current Exceed Limit',
        related='float_request_id.exceed_limit',
        readonly=True,
        store=True,
    )

    current_float_manager_id  = fields.Many2one(
        'res.users',
        string='Current Float Manager',
        related='float_request_id.float_manager_id',
        readonly=True,
        store=True,
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
    
    modify_cross_department = fields.Boolean(
        string='Change Cross Department Permission?',
        default=False,
        tracking=True,
        help='Check to change cross department transaction permission'
    )

    new_allow_cross_department = fields.Boolean(
        string='New Allow Cross Department',
        tracking=True,
        help='New setting for cross department transaction permission'
    )
    
    modify_exceed_margin = fields.Boolean(
        string='Modify Exceed Margin?',
        default=False,
        tracking=True,
        help='Check to modify the exceed margin'
    )
    
    new_exceed_margin_percentage = fields.Float(
        string='New Exceed Margin (%)', 
        default=10.0,
        tracking=True,
        help='New exceed margin percentage (e.g., 10 for 10%)'
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
        ('cancelled', 'Cancelled'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)
    
    state_display = fields.Char(
        string='Status Display',
        compute="_compute_state_display",
        help="Readable state display",
    )
    
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
    
    rejected_by = fields.Many2one(
        'res.users',
        string='Rejected By',
        readonly=True,
        tracking=True
    )
    
    rejection_date = fields.Datetime(
        string='Rejection Date',
        readonly=True
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        help='Reason for rejection'
    )
    
    remarks = fields.Text(
        string='Remarks',
        help='Additional comments'
    )
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)
    
    
    expected_completion_date = fields.Date(
        string='Expected Completion Date',
        help='When this customization is expected to be completed',
    )
    
    @api.depends('state')
    def _compute_state_display(self):
        """Compute human-readable state display"""
        for record in self:
            record.state_display = record.state.replace('_', ' ').title()
    
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
            
    @api.onchange('modify_float_manager')
    def _onchange_modify_float_manager(self):
        """Clear new float manager when unchecked"""
        if not self.modify_float_manager:
            self.new_float_manager_id = False
    
    @api.onchange('modify_cross_department')
    def _onchange_modify_cross_department(self):
        """Clear cross department setting when unchecked"""
        if not self.modify_cross_department:
            self.new_allow_cross_department = False
    
    @api.onchange('modify_exceed_margin')
    def _onchange_modify_exceed_margin(self):
        """Clear exceed margin when unchecked"""
        if not self.modify_exceed_margin:
            self.new_exceed_margin_percentage = 10.0
    
    @api.onchange('new_can_exceed')
    def _onchange_new_can_exceed(self):
        """Clear exceed limit when can_exceed is unchecked"""
        if not self.new_can_exceed:
            self.new_exceed_limit = 0.0
            
    @api.constrains('new_float_amount', 'new_exceed_limit', 'new_exceed_margin_percentage')
    def _check_amounts(self):
        """Validate amount fields"""
        for record in self:
            if record.modify_float_amount and record.new_float_amount <= 0:
               raise ValidationError(_('New float amount must be greater than zero.'))
            if record.modify_can_exceed and record.new_can_exceed and record.new_exceed_limit <= 0:
                raise ValidationError(_('New exceed limit must be greater than zero.'))
            if record.modify_exceed_margin and (record.new_exceed_margin_percentage < 0 or record.new_exceed_margin_percentage > 100):
                raise ValidationError(_('New exceed margin percentage must be between 0 and 100.'))

    @api.constrains('modify_float_amount', 'modify_can_exceed', 'modify_float_manager', 
                    'modify_cross_department', 'modify_exceed_margin')
    def _check_modifications(self):
        """Ensure at least one modification is selected"""
        for record in self:
            modifications = [
                record.modify_float_amount, 
                record.modify_can_exceed, 
                record.modify_float_manager,
                record.modify_cross_department,
                record.modify_exceed_margin
            ]
            if not any(modifications):
                raise ValidationError(_('Please select at least one modification to make.'))

    @api.constrains('float_request_id')
    def _check_pending_customizations(self):
        """Check for existing pending customizations"""
        for record in self:
            if record.float_request_id:
                existing = self.search([
                    ('float_request_id', '=', record.float_request_id.id),
                    ('state', 'in', ['draft', 'requested']),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('There are already pending customizations for float "%s". '
                          'Please resolve them before creating new ones.') % record.float_request_id.name)

    def action_submit(self):
        """Submit request for approval - Enhanced with proper group checks"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            
            # Check if user can submit (should be Float Manager or higher)
            can_submit = any([
                self.env.user.has_group('petty-cash.group_petty_cash_float_manager'),
                self.env.user.has_group('petty-cash.group_petty_cash_manager'),
                self.env.user.has_group('petty-cash.group_petty_cash_accountant'),
                self.env.user.has_group('base.group_system'),
            ])
            
            if not can_submit:
                raise UserError(_('You do not have permission to submit customization requests. Contact your Float Manager or System Administrator.'))
            
            record.state = 'requested'
            
            # Client notification (more reliable than message_post)
            record.message_post(
                body=_('Float customization request submitted for approval.'),
                message_type='notification'
            )
            
            record._send_approval_notification()
            
            # Return success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Float customization request submitted for approval.'),
                    'type': 'success',
                }
            }
            
    def _send_approval_notification(self):
        """Send notification to managers for approval"""
        self.ensure_one()
        
        # FIXED: Use your custom petty cash groups instead of account.group_account_manager
        approver_groups = [
            'petty-cash.group_petty_cash_accountant',  # Your accountant group
            'petty-cash.group_petty_cash_manager',     # Your manager group
        ]
        
        approvers = self.env['res.users']
        for group_xmlid in approver_groups:
            try:
                group = self.env.ref(group_xmlid, raise_if_not_found=False)
                if group and group.users:
                    approvers |= group.users
            except:
                continue
        
        # Also include system administrators
        try:
            admin_group = self.env.ref('base.group_system', raise_if_not_found=False)
            if admin_group and admin_group.users:
                approvers |= admin_group.users
        except:
            pass
        
        # Create activities for all approvers
        for approver in approvers:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=approver.id,
                summary=f'Float Customization Approval Required - {self.float_request_id.name}',
                note=f'Please review and approve the customization request for float: {self.float_request_id.name}'
            )
                
    @api.model
    def get_system_configurations(self):
        """Get system configuration parameters for customizations"""
        return {
            'allow_exceed_modifications': self.env['ir.config_parameter'].sudo().get_param(
                'petty_cash.allow_exceed_modifications', default=True
            ),
            'require_manager_approval': self.env['ir.config_parameter'].sudo().get_param(
                'petty_cash.require_manager_approval', default=True
            ),
            'max_modification_percentage': float(
                self.env['ir.config_parameter'].sudo().get_param(
                    'petty_cash.max_modification_percentage', default=50.0
                )
            ),
            'auto_approve_minor_changes': self.env['ir.config_parameter'].sudo().get_param(
                'petty_cash.auto_approve_minor_changes', default=False
            ),
        }

    def action_approve(self):
        """Approve the customization request"""
        for record in self:
            if record.state != 'requested':
                raise UserError(_('Only requested customizations can be approved.'))
            
            # FIXED: Check for your custom petty cash groups instead of account manager
            has_permission = any([
                self.env.user.has_group('petty-cash.group_petty_cash_accountant'),
                self.env.user.has_group('petty-cash.group_petty_cash_manager'),
                self.env.user.has_group('base.group_system'),  # System admin
            ])
            
            if not has_permission:
                raise UserError(_('You do not have permission to approve customizations. Required groups: Petty Cash Accountant, Petty Cash Manager, or System Administrator.'))
            
            # Rest of your approval logic stays the same...
            float_record = record.float_request_id
            changes = []
            
            # Apply changes and build change log
            if record.modify_float_amount:
                old_amount = float_record.initial_amount
                float_record.initial_amount = record.new_float_amount
                changes.append(f'Float amount: {old_amount} → {record.new_float_amount}')
                
            if record.modify_can_exceed:
                old_can_exceed = float_record.can_exceed
                float_record.can_exceed = record.new_can_exceed
                if record.new_can_exceed and record.new_exceed_limit:
                    float_record.exceed_limit = record.new_exceed_limit
                    changes.append(f'Exceed permission: {old_can_exceed} → {record.new_can_exceed} (Limit: Rs. {record.new_exceed_limit})')
                else:
                    changes.append(f'Exceed permission: {old_can_exceed} → {record.new_can_exceed}')
               
            if record.modify_float_manager:
                old_manager = float_record.float_manager_id.name if float_record.float_manager_id else 'None'
                float_record.float_manager_id = record.new_float_manager_id
                new_manager = record.new_float_manager_id.name if record.new_float_manager_id else 'None'
                changes.append(f'Float manager: {old_manager} → {new_manager}')
            
            if record.modify_cross_department:
                old_cross_dept = float_record.allow_cross_department_request
                float_record.allow_cross_department_request = record.new_allow_cross_department
                changes.append(f'Cross-department access: {old_cross_dept} → {record.new_allow_cross_department}')
            
            if record.modify_exceed_margin:
                old_margin = float_record.exceed_margin_percentage
                float_record.exceed_margin_percentage = record.new_exceed_margin_percentage
                changes.append(f'Exceed margin: {old_margin}% → {record.new_exceed_margin_percentage}%')
            
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
            
            # Complete any pending activities
            record._complete_approval_activities()


    def _complete_approval_activities(self):
        """Complete any pending activities after approval"""
        for record in self:
            self.ensure_one()
            activities = self.activity_ids.filtered(lambda a: a.activity_type_id.name == 'Todo')
            activities.action_done()
           

    def action_reject(self):
        """Reject the customization request"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Customization',
            'res_model': 'float.customization.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_customization_id': self.id},
        }
        
    def _do_reject(self, reason=''):
        """Internal method to perform rejection"""
        for record in self:
            if record.state != 'requested':
                raise UserError(_('Only requested customizations can be rejected.'))
            
            record.state = 'rejected'
            record.rejected_by = self.env.user
            record.rejection_date = fields.Datetime.now()
            record.rejection_reason = reason
            
            record.message_post(
                body=_('Float customization request rejected by %s\nReason: %s') % (self.env.user.name, reason),
                message_type='notification'
            )
            
            # Complete any pending activities
            record._complete_approval_activities()
            
    def action_reset_to_draft(self):
        """Reset to draft state"""
        for record in self:
            if record.state != 'rejected':
                raise UserError(_('Only rejected requests can be reset to draft.'))
            record.state = 'draft'
            record.rejected_by = False
            record.rejection_date = False
            record.rejection_reason = False
            
    def action_cancel(self):
        """Cancel the customization request"""
        for record in self:
            if record.state not in ['draft', 'requested']:
                raise UserError(_('Only draft or requested customizations can be cancelled.'))
            record.state = 'cancelled'
            record.message_post(
                body=_('Float customization request cancelled by %s') % self.env.user.name,
                message_type='notification'
            )
            
    def action_duplicate(self):
        """Create a duplicate customization request"""
        self.ensure_one()
        
        new_customization = self.copy({
            'state': 'draft',
            'approved_by': False,
            'approval_date': False,
            'rejected_by': False,
            'rejection_date': False,
            'rejection_reason': False,
            'request_date': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Float Customization',
            'res_model': 'float.customization',
            'res_id': new_customization.id,
            'view_mode': 'form',
            'target': 'current',
        }
            
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name = f"{record.float_request_id.name} - {record.state_display}"
            result.append((record.id, name))
        return result
    
    @api.model
    def create(self, vals):
        """Override create to add sequence or auto-naming"""
        res = super().create(vals)
        res.message_post(
            body=_('Float customization request created for %s') % res.float_request_id.name,
            message_type='notification'
        )
        return res
    
    def write(self, vals):
        """Enhanced write method with notifications"""
        old_states = {record.id: record.state for record in self}
        res = super().write(vals)

        if 'state' in vals:
            for record in self:
                old_state = old_states.get(record.id)
                if old_state != record.state and record.state == 'requested':
                    record._send_approval_notification()

        return res
    
    def action_create_detailed(self):
        """Create detailed customization request from wizard"""
        self.ensure_one()
    
        # Validate that at least one modification is selected
        if not any([self.modify_float_amount, self.modify_can_exceed, self.modify_float_manager]):
            raise UserError(_('Please select at least one modification.'))
    
        # Return to detailed form view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Float Customization Details',
            'res_model': 'float.customization',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }
        
    def action_reset_form(self):
        """Reset form fields to default state"""
        self.ensure_one()
    
        if self.state != 'draft':
            raise UserError(_('Only draft requests can be reset.'))
    
        # Reset all modification flags and values
        self.write({
            'modify_float_amount': False,
            'new_float_amount': 0.0,
            'modify_can_exceed': False,
            'new_can_exceed': False,
            'new_exceed_limit': 0.0,
            'modify_float_manager': False,
            'new_float_manager_id': False,
            'modify_cross_department': False,
            'new_allow_cross_department': False,
            'modify_exceed_margin': False,
            'new_exceed_margin_percentage': 10.0,
            'reason_for_change': '',
            'remarks': '',
        })
    
        return True
    
    
class FloatCustomizationRejectWizard(models.TransientModel):
    _name = 'float.customization.reject.wizard'
    _description = 'Float Customization Rejection Wizard'
    
    customization_id = fields.Many2one(
        'float.customization',
        string='Customization',
        required=True,
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help='Please provide a reason for rejection'
    )
    
    def action_reject(self):
        """Perform the rejection"""
        self.ensure_one()
        self.customization_id._do_reject(self.rejection_reason)
        return {'type': 'ir.actions.act_window_close'}