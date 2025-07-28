from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError


class FloatRequest(models.Model):
    _name = 'float.request'
    _description = 'Float Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Float Name',
        required=True,
        tracking=True,
    )
    
    # department_id = fields.Many2one(
    #     'hr.department',
    #     string='Department',
    #     required=True,
    #     tracking=True,
    # )
    
    initial_amount = fields.Float(
        string='Initial Float Amount',
        required=True,
        tracking=True,
    )
    
    can_exceed = fields.Boolean(
        string='Can Exceed over the Initial Amount?',
        default=False,
        tracking=True,
    )
    
    float_manager_id = fields.Many2one(
        'res.users',
        string='Float Manager',
        required=True,
        default=lambda self: self.env.user,
    )
    
    date_created = fields.Date(
        string='Date',
        readonly=True,
        default=fields.Date.today,
    )
    
    remarks = fields.Text(
        string='Remarks',
    )
    
    attachment = fields.Binary(
        string='Attachment',
        
    )
    
    attachment_filename = fields.Char(
        string='Attachment Filename',
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
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
        store=False,
    )
    
    total_petty_cash_requests = fields.Integer(
        string= 'Total Petty Cash Requests',
        compute='_compute_request_totals',
        store=False,
    )
    
    @api.depends()
    def _compute_request_totals(self):
        for record in self:
            record.total_iou_requests = len(record.iou_request_id)
            record.total_petty_cash_requests = len(record.petty_cash_request_id)


    def action_submit(self):
        self.state = 'requested'
    
    def action_approve(self):
        if self.state != 'requested':
            raise UserError(_('Only requests in "Requested" state can be approved.'))
        self.state = 'approved'
    
    def action_reject(self):
        if self.state != 'requested':
            raise UserError(_('Only requests in "Requested" state can be rejected.'))
        self.state = 'rejected'
    
        