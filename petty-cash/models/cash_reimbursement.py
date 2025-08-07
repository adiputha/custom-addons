from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class CashReimbursement(models.Model):
    _name = 'cash.reimbursement'
    _description = 'Cash Reimbursement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'request_date desc, id desc'
    
    name = fields.Char(
        string='Reimbursement Number',
        required=True,
        copy=False,
        readonly=True,
        tracking=True,
    )
    
    float_request_id = fields.Many2one(
        'float.request',
        string="Float",
        required=True,
        tracking=True,
        domain="[('state', 'in', ['approved'])]",
        help="Select the float request for which reimbursement is being made.",
    )
    
    request_date = fields.Datetime(
        string='Request Date',
        required=True,
        readonly=True,
        default=lambda self: fields.Datetime.now(),
        tracking=True,
        help="The date and time when the reimbursement request was made.",
    )
    
    handler_name = fields.Many2one(
        'res.users',
        string='Handler Name',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    
    current_balance = fields.Float(
        string='Current Balance',
        related='float_request_id.cash_in_hand',
        readonly=True,
        tracking=True,
    )
    
    required_amount = fields.Float(
        string='Required Amount for Reimbursement',
        required=True,
        tracking=True,
        help="The amount requested for reimbursement.",
    )
    
    received_amount = fields.Float(
        string='Received Amount',
        tracking=True,
        help="The amount actually received as reimbursement.",
    )

    justification = fields.Text(
        string='Justification',
        required=True,
        tracking=True,
        help="Provide a justification for the reimbursement request.",
    )
    
    attachment = fields.Binary(
        string='Attachment',
        help="Attach any relevant documents or files related to the reimbursement request.",
    )
    
    attachment_filename = fields.Char(
        string='Attachment Filename',
        
    )
    
    remarks = fields.Text(
        string='Remarks',
        help="Any additional remarks or comments regarding the reimbursement request.",
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Aproval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)

    is_manager_approved = fields.Boolean(
        string='Float Manager Approved',
        default=False,
        tracking=True,
    )
    
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        tracking=True,
        help="User who approved the reimbursement request.",
    )
    
    cash_received_by_handler = fields.Boolean(
        string='Cash Received by Handler',
        default=False,
        tracking=True,
        help="Indicates if the handler has received the cash for reimbursement.",
    )
    
    received_voucher = fields.Binary(
        string='Received Voucher',
        help="Attach the received voucher for the reimbursement."
    )
    
    received_voucher_filename = fields.Char(
        string='Received Voucher Filename',
    )
    
    report_from_date = fields.Date(
        string='Report From Date',
        help='Start date for expense report generation'
    )
    
    report_to_date = fields.Date(
        string='Report To Date',
        help='End date for expense report generation'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New Reimbursement Request') == 'New Reimbursement Request':
                vals['name'] = self._generate_sequence_number()
        return super().create(vals_list)
    
    def _generate_sequence_number(self):
        """Generate a unique sequence number for the reimbursement request."""
        sequence = self.env['ir.sequence'].next_by_code('cash.reimbursement')
        if not sequence:
            year = fields.Date.today().strftime('%Y')
            last_reimb = self.search([], order='id desc', limit=1)
            if last_reimb and last_reimb.name.startswith('CS-'):
                try:
                    last_num = int(last_reimb.name.split('-')[1])
                    return f'CS-{year}-{str(last_num + 1).zfill(3)}'
                except:
                    pass
            return f'CS-{year}-001'
        return sequence
    
    @api.constains('required_amount', 'received_amount')
    def _check_amounts(self):
        for record in self:
            if record.required_amount <= 0:
                raise ValidationError(_("Required amount must be greater than zero."))
            if record.received_amount < 0:
                raise ValidationError(_("Received amount cannot be negative."))
            
    
    def action_submit(self):
        """Submit reimbursement request for approval"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only draft requests can be submitted."))
            record.state = 'pending'
            record.message_post(
                body=_("Reimbursement request submitted for approval."),
                message_type='notification',
            )
            
    def action_approve(self):
        """Approve the reimbursement request"""
        for record in self:
            if record.state != 'pending':
                raise UserError(_("Only pending requests can be approved."))
            record.write({
                'state': 'approved',
                'is_manager_approved': True,
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
            record.message_post(
                body=_("Reimbursement request approved by %s.") % self.env.user.name,
                message_type='notification',
            )
            
    def action_reject(self):
        """Reject the reimbursement request"""
        for record in self:
            if record.state != 'pending':
                raise UserError(_("Only pending requests can be rejected."))
            record.state = 'rejected'
            record.message_post(
                body=_("Reimbursement request rejected."),
                message_type='notification',
            )
            
    def action_complete_request(self):
        """Mark the reimbursement request as completed"""
        for record in self:
            if record.state != 'approved':
                raise UserError(_("Only approved requests can be marked as completed."))
            if not record.cash_received_by_handler:
                raise UserError(_("Cash must be received by the handler before completing the request."))
            if not record.received_amount:
                raise UserError(_("Please enter the Received amount."))

            record.state = 'completed'
            record.message_post(
                body=_("Reimbursement request completed."),
                message_type='notification',
            )
            
    def action_update_denomination(self):
        self.ensure_one()
        if not self.state in ['approved']:
            raise UserError(_("Only approved requests can update the denomination."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Update Denomination'),
            'res_model': 'cash.denomination.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reimbursement_id': self.id,
                'default_received_amount': self.required_amount or self.received_amount,
            },
        }
        
    def action_reset_to_draft(self):
        """Reset the reimbursement request to draft state"""
        for record in self:
            if record.state not in ['pending']:
                raise UserError(_("Only pending requests can be reset to draft."))
            record.state = 'draft'
            record.write({
                'is_manager_approved': False,
                'approved_by': False,
                'cash_received_by_handler': False,
                'received_amount': 0.0,
                'received_voucher': False,
                'received_voucher_filename': False,
            })
            
            
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name} - {record.float_request_id.name}"
            if record.required_amount:
                name += f" (Req: {record.required_amount:,.2f})"
            result.append((record.id, name))
        return result
    
    