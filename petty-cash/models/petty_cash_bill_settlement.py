from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class PettyCashBillSettlement(models.Model):
    _name = "petty.cash.bill.settlement"
    _description = "Petty Cash Bill Settlement"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date desc"

    petty_cash_request_id = fields.Many2one(
        'petty.cash.request',
        string="Petty Cash Request",
        required=True,
        ondelete='cascade',
    )
    
    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.context_today,
        help="Date of the settlement",
    )

    category = fields.Many2one(
        'petty.cash.category',
        string="Category",
        required=True,
    )
    
    amount = fields.Float(
        string="Amount",
        required=True,
        help="Amount of the bill/expenses",
    )

    attach_receipt = fields.Binary(
        string="Receipt",
        required=True,
        help="Attach the receipt for the bill/expenses",
    )
    
    receipt_filename = fields.Char(
        string="Receipt Filename",
    )

    description = fields.Text(
        string="Description",
        help="Additional remarks or notes regarding the settlement",
    )
    
    status = fields.Selection(
        [   
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string="Status",
        default='draft',
        tracking=True,
    )
    
    action = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string="Action", help="Select action for bill approval/rejection")
    
    approved_by = fields.Many2one(
        'res.users',
        string="Approved By",
        tracking=True,
    )
    
    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
        tracking=True,
    )
    
    rejected_by = fields.Many2one(
        'res.users',
        string="Rejected By",
        tracking=True,
    )

    rejection_date = fields.Datetime(
        string="Rejection Date",
        readonly=True,
        tracking=True,
    )

    rejection_reason = fields.Text(
        string="Rejection Reason",
        help="Reason for rejection if the settlement is rejected",
    )
    
    @api.onchange('action')
    def _onchange_action(self):
        """Update the status based on the action taken."""
        pass
            
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_("The amount must be positive."))
            
    def action_approve(self):
        """Approve bill settlement"""
        for record in self:
            if record.status != 'submitted':
                raise ValidationError(_("Only submitted bills can be approved."))
            
            record.write({
                'status': 'approved',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'action': False
            })
            
            record.message_post(
                body=_("Bill approved by %s") % self.env.user.name,
                message_type='notification',
            )
            
    def action_reject(self):
        """Reject bill settlement"""
        for record in self:
            if record.status != 'submitted':
                raise ValidationError(_("Only submitted bills can be rejected."))
            
            if not record.rejection_reason:
                raise ValidationError(_("Please provide a reason for rejection."))
            
            record.write({
                'status': 'rejected',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'action': False
            })

            record.message_post(
                body=_("Bill rejected by %s. Reason: %s") % (self.env.user.name, record.rejection_reason),
                message_type='notification',
            )
            
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            status_icon = ""
            if record.status == 'approved':
                status_icon = "✅ "
            elif record.status == 'rejected':
                status_icon = "❌ "
            elif record.status == 'draft':
                status_icon = "📝 "
            
        name = f"{status_icon}{record.category.name if record.category else 'No Category'} - Rs. {record.amount:,.2f}"
        if record.date:
            name = f"{record.date} - {name}"
        result.append((record.id, name))
        return result
    
    # @api.model
    # def create(self, vals):
    #     """Override create to handle parent state"""
    #     result = super().create(vals)
    #     return result