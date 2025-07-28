from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class IouRequest(models.Model):
    _name = 'petty.cash.iou.request'
    _description = 'IOU Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'  # Use 'name' as the display name in views

    name = fields.Char(
        string= 'IOU Request Number',
        readonly=True,
        default='New IOU Request',
        tracking=True,
    )
    
    request_type = fields.Selection(
        ('iou', 'IOU'),
        string='Request Type',
        required=True,
        default='iou',
    )
    
    state= fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('cash_issued', 'Cash Issued'),
        ('cancelled', 'Cancelled'),
        ('pending_bill_submission', 'Pending Bill Submission'),
        ('completed', 'Completed'),
        ('hod_approval_pending', 'HOD Approval Pending'),
        ('float_manager_approval_pending', 'Float Manager Approval Pending'),
        ('hod_approved', 'HOD Approved'),
        ('float_manager_approved', 'Float Manager Approved'),
        ('hod_rejected', 'HOD Rejected'),
        ('float_manager_rejected', 'Float Manager Rejected'),
    ], string='Status', default='draft', tracking=True) 
    
    request_by = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        tracking=True,
    )
    
    request_date = fields.Datetime(
        string='Request Date',
        default=lambda self: datetime.now(),
        tracking=True,
        required=True,
    )
    
    due_date = fields.Datetime(
        string='Due Date',
        compute='_compute_due_date',
        readonly=True,
        store=True,
    )
    
    request_voucher = fields.Binary(
        string='Request Voucher',
        attachment=True,
        help='Upload request voucher for IOU request',
    )
    
    request_voucher_name = fields.Char(
        string='Voucher Filename',
    )
    
    reason_in_advance = fields.Text(
        string='Reason in Advance',
        required=True,
        tracking=True,
        help='Provide a reason for requesting the IOU in advance.',
    )
    
    request_amount = fields.Float(
        string='Request Amount',
        required=True,
        tracking=True,
        default=0.0,
    )
    
    isHodApproved = fields.Boolean(
        string='HOD Approved',
        default=False,
        tracking=True,
    )
    
    hodApprovedBy = fields.Many2one(
        'res.users',
        string='HOD Approved By',
        tracking=True,
    )
    
    isFloatManagerApproved = fields.Boolean(
        string='Float Manager Approved',
        default=False,
        tracking=True,
    )
    
    floatManagerApprovedBy = fields.Many2one(
        'res.users',
        string='Float Manager Approved By',
        tracking=True,      
    )
    
    cashReceivedByEmployee = fields.Boolean(
        string='Cash Received by Employee',
        default=False,
        tracking=True,
    )
    
    received_voucher = fields.Binary(
        string='Received Voucher',
        attachment=True,
        help='Upload voucher for cash received by employee',
    )
    
    received_voucher_name = fields.Char(
        string='Received Voucher Filename',
    )
    
    remarks = fields.Text(
        string='Remarks',
        help='Additional remarks or comments regarding the petty cash request',
    )
    
    bill_ids = fields.One2many(
        'iou.bill.settlement',
        'iou_request_id',
        string='Bill Settlements',
    )
    
    settlement_amount = fields.Float(
        string='Settlement Amount',
        compute='_compute_settlement_amount',
        store=True,
    )
    
    settlement_date = fields.Datetime(
        string='Settlement Date',
        compute='_compute_settlement_date',
        store=True,
    )
    
    float_request_id = fields.Many2one(
        'float.request',
        string='Float name',
        required=True,
        help='Select the float which you want to use for this petty cash request',
        tracking=True, 
    )
    
    
    
    @api.depends('bill_ids.amount', 'bill_ids.status')
    def _compute_settlement_amount(self):
        """Compute the total settlement amount from related bills"""
        for record in self:
            appproved_bills = record.bill_ids.filtered(lambda b: b.status == 'approved')
            record.settlement_amount = sum(appproved_bills.mapped('amount'))
            
    @api.depends('bill_ids.date', 'bill_ids.status')
    def _compute_settlement_date(self):
        """Compute the latest settlement date from approved bills"""
        for record in self:
            approved_bills = record.bill_ids.filtered(lambda b: b.status == 'approved')
            if approved_bills:
                record.settlement_date = max(approved_bills.mapped('date'))
            else:
                record.settlement_date = False
    
    def action_approve_selected(self):
        """Action to approve selected IOU requests"""
        self.ensure_one()
        pending_bills = self.bill_ids.filtered(lambda b: b.action == 'approve' and b.status == 'pending')
        pending_bills.write({'status': 'approved', 'action': False})
        
        if pending_bills:
            self.message_post(
                body=_("Selected bills approved successfully."),
            )
            
        return True
    
    def action_reject_selected(self):
        """Action to reject selected IOU requests"""
        self.ensure_one()
        pending_bills = self.bill_ids.filtered(lambda b: b.action == 'reject' and b.status == 'pending')
        bills_without_remarks = pending_bills.filtered(lambda b: not b.remarks)
        
        if bills_without_remarks:
            raise UserError(_("Please provide remarks for the bills you are rejecting."))
        pending_bills.write({'status': 'rejected', 'action': False})
        
        if pending_bills:
            self.message_post(
                body=_("Rejected %d bills totaling Rs. %.2f") % 
                (len(pending_bills), sum(pending_bills.mapped('amount')))
            )
            
        return True
            
    def action_complete_iou(self):
        """Action to complete the IOU request"""
        self.ensure_one()
        if abs(self.settlement_amount - self.request_amount) > 0.01:
            raise UserError(_("Settlement amount (%.2f) must equal request amount (%.2f) to complete IOU.") % (self.settlement_amount, self.request_amount))
        
        self.state = 'completed'
        self.message_post(body=_("IOU request completed successfully."))
        return True
    
    @api.depends('request_date')
    def _compute_due_date(self):
        default_days = int(self.env['ir.config_parameter'].sudo().get_param('iou.due.days', 10))
        for record in self:
            if record.request_date:
                record.due_date = record.request_date + timedelta(days=default_days)
            else:
                record.due_date = False
                
    @api.model
    def set_iou_due_days(self, days):
        """Method to set IOU due days"""
        self.env['ir.config_parameter'].sudo().set_param('iou.due.days', days)
        return True
    
    @api.model
    def get_iou_due_days(self):
        """Method to get IOU due days"""
        return int(self.env['ir.config_parameter'].sudo().get_param('iou.due.days', 10))
        
    def action_submit(self):
        """Action to submit the IOU request"""
        self.ensure_one()
        if self.state == 'draft':
            self.state = 'requested'
            self.message_post(body=_("IOU request submitted successfully."))
        return True
    
    def action_cancel(self):
        """Action to cancel the IOU request"""
        self.ensure_one()
        if self.state in ['draft', 'requested']:
            self.state = 'cancelled'
            self.message_post(body=_("IOU request cancelled."))
        else:
            raise UserError(_("You can only cancel a request in draft or requested state."))
        return True
    
    def action_cash_issued(self):
        """Action to mark cash as issued to employee and denomination"""
        self.ensure_one()
        if self.state == 'requested':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Cash Denomination - IOU',
                'res_model': 'cash.denomination.wizard',
                'view_mode': 'form',
                #'view_id': self.env.ref('petty_cash_iou_request.cash_denomination_iou_wizard_form'),
                'target': 'new',
                'context': {
                    'default_iou_request_id': self.id,
                    'default_request_amount': self.request_amount,
                    'default_request_type': self.request_type,
                }
            }
        else:
            raise UserError(_("You can only issue cash for requests in the requested state."))
        return True
    
    def action_complete_request(self):
        """Action to mark the IOU request as completed"""
        self.ensure_one()
        if self.state in ['hod_approved', 'float_manager_approved']:
            self.ensure_one()
            if self.state != 'pending_bill_submission':
                raise UserError(_("You can only complete requests that are in pending bill submission state."))
            
            self.state = 'completed'
            self.message_post(body=_("IOU request completed successfully."))
            return True
    

    

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New IOU Request') == 'New IOU Request':
                vals['name'] = self._generate_sequence_number('petty.cash.iou.request')
        return super().create(vals_list)

    def _generate_sequence_number(self, sequence_code):
        """Generate sequence number with proper error handling"""
        sequence = self.env['ir.sequence'].next_by_code(sequence_code)
        if not sequence:
            # If sequence doesn't exist, create a temporary one
            year = fields.Date.today().strftime('%y')
            if sequence_code == 'petty.cash.iou.request':
                # Find the last IOU number
                last_iou = self.search([('request_type', '=', 'iou')], order='id desc', limit=1)
                if last_iou and last_iou.name.startswith('IOU-'):
                    try:
                        last_num = int(last_iou.name.split('-')[-1])
                        return f'IOU-{year}-{str(last_num + 1).zfill(3)}'
                    except:
                        pass
                return f'IOU-{year}-001'
            else:
                # Find the last PC number
                last_pc = self.search([('request_type', '=', 'petty_cash')], order='id desc', limit=1)
                if last_pc and last_pc.name.startswith('PC-'):
                    try:
                        last_num = int(last_pc.name.split('-')[-1])
                        return f'PC-{year}-{str(last_num + 1).zfill(3)}'
                    except:
                        pass
                return f'PC-{year}-001'
        return sequence
    
    
    #bill submissions for iou 
    def action_submit_bills(self):
        """Action to submit bills for IOU request"""
        self.ensure_one()
        if self.state != 'pending_bill_submission':
            raise UserError(_("You can only submit bills for requests in pending bill submission state."))
        
        draft_bills = self.bill_ids.filtered(lambda b: b.status == 'draft')
        if not draft_bills:
            raise UserError(_("No draft bills found for this IOU request."))
        
        total_bill_amount = sum(draft_bills.mapped('amount'))
        if abs(total_bill_amount - self.request_amount) > 0.01:
            raise UserError(_("Total bill amount (%.2f) must equal request amount (%.2f) to submit bills.") % (total_bill_amount, self.request_amount))
        
        draft_bills.write({'status': 'submitted'})
        
        self.message_post(
            body=_("Bills submitted successfully. Total amount: %.2f") % total_bill_amount,
            message_type='notification',
        )
        return True
    
    
    @api.constrains('request_amount', 'due_date', 'request_date','isHodApproved', 'hodApprovedBy', 'isFloatManagerApproved', 'floatManagerApprovedBy', 'float_request_id')
    def _check_fields(self):
        """Ensure the fields are set correctly"""
        for record in self:
            errors = []
            if record.request_amount <= 0:
                errors.append(_('Request amount must be greater than zero. Please enter a valid amount.'))
            if record.due_date and record.request_date and record.due_date < record.request_date:
                errors.append(_('Due date cannot be earlier than request date. Please select a valid due date.'))
            if not record.isHodApproved:
                errors.append(_('HOD Approved must be ticked'))
            if record.isHodApproved and not record.hodApprovedBy:
                errors.append(_('Select the approved HOD.'))
            if not record.isFloatManagerApproved:
                errors.append(_('Float Manager Approved must be ticked'))
            if record.isFloatManagerApproved and not record.floatManagerApprovedBy:
                errors.append(_('Select the Approved Float Manager.'))
            if not record.float_request_id:
                errors.append(_('Please select a float for this petty cash request.'))
            if errors:
                raise ValidationError('Please fix the following:\n' + '\n'.join(errors))
    
       