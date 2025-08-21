from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


import logging
from PIL import Image
from pdf2image import convert_from_bytes

_logger = logging.getLogger(__name__)


class PettyCashRequest(models.Model):
    _name = "petty.cash.request"
    _description = "Petty Cash Request"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _order = "request_date desc, name desc"
    _rec_name = "name"  # Use 'name' as the display name in views

    name = fields.Char(
        string="Request Number",
        copy=False,
        readonly=True,
        default="New Petty Cash Request",
        tracking=True,
    )

    request_type = fields.Selection(
        [
            ("petty_cash", "Petty Cash"),
            ("iou", "IOU"),
        ],
        string="Request Type",
        required=True,
        default="petty_cash",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("pending_bill_submission", "Pending Bill Submission"),
            ("cancelled", "Cancelled"),
            ("cash_issued", "Cash Issued"),
            ("completed", "Completed"),
            ("hod_approval_pending", "HOD Approval Pending"),
            ("float_manager_approval_pending", "Float Manager Approval Pending"),
            ("hod_approved", "HOD Approved"),
            ("float_manager_approved", "Float Manager Approved"),
            ("hod_rejected", "HOD Rejected"),
            ("float_manager_rejected", "Float Manager Rejected"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    request_by = fields.Many2one(
        "res.users",
        string="Request By",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )

    # employee_dept = fields.Many2one(
    #     'hr.department',
    #     string='Employee Department',
    #     compute='_compute_employee_dept',
    #     store=True,
    #     readonly=True
    # )

    request_date = fields.Datetime(
        string="Request Date", default=fields.Datetime.now, required=True, tracking=True
    )

    due_date = fields.Datetime(
        string="Due Date",
        compute="_compute_due_date",
        readonly=True,
        store=True,
    )

    request_voucher = fields.Binary(
        string="Request Voucher",
        attachment=True,
        help="Upload manually signed request voucher",
    )

    request_voucher_filename = fields.Char(string="Request Voucher Filename")

    request_amount = fields.Float(
        string="Request Amount",
        required=True,
        default=0.0,
        tracking=True,
    )

    float_request_id = fields.Many2one(
        "float.request",
        string="Float name",
        required=True,
        help="Select the float which you want to use for this petty cash request",
        tracking=True,
    )

    # Approval Fields
    isHodApproved = fields.Boolean(
        string="HOD Approved",
        default=False,
        tracking=True,
    )

    hodApprovedBy = fields.Many2one(
        "res.users",
        string="HOD Approved By",
        tracking=True,
    )

    isFloatManagerApproved = fields.Boolean(
        string="Float Manager Approved",
        default=False,
        tracking=True,
    )

    floatManagerApprovedBy = fields.Many2one(
        "res.users",
        string="Float Manager Approved By",
        tracking=True,
    )

    category = fields.Many2one(
        "petty.cash.category",
        string="Category",
        required=True,
        tracking=True,
        help="Select the category for this petty cash request",
    )
    
    description = fields.Text(
        string="Description",
        required=True,
        help="Provide a brief description of the petty cash request",
    )

    # Cash Handling
    cashReceivedByEmployee = fields.Boolean(
        string="Cash Received By",
        default=False,
        tracking=True,
    )

    received_voucher = fields.Binary(
        string="Received Voucher",
        attachment=True,
        help="Upload Received voucher",
    )

    received_voucher_filename = fields.Char(string="Received Voucher Filename")

    remark = fields.Text(
        string="Remark",
        help="Additional remarks or comments regarding the petty cash request",
    )
    
    bill_settlement_ids = fields.One2many(
        "petty.cash.bill.settlement",
        "petty_cash_request_id",
        string="Bill Settlements",
        help="List of bill settlements related to this petty cash request"
    )
    
    settlement_amount = fields.Float(
        string= 'Settlement Amount',
        compute='_compute_settlement_amount',
        store=True,
        help="Total amount of all related bill settlements"
    )
    
    settlement_date = fields.Datetime(
        string='Settlement Date',
        compute='_compute_settlement_date',
        store=True,
        help="Latest settlement date from approved bills"
    )
    
    has_pending_bills = fields.Boolean(
        string='Has Pending Bills',
        compute='_compute_has_pending_bills',
        help='True if there are bills pending approval'
    )
    
    reason_in_advance = fields.Text(
        string='Reason for Advance',
        help="Reason for requesting advance payment (for IOU requests)"
    )
    
    @api.depends('bill_settlement_ids.amount', 'bill_settlement_ids.status')
    def _compute_settlement_amount(self):
        """Compute the total settlement amount from approved bills"""
        for record in self:
            approved_bills = record.bill_settlement_ids.filtered(lambda b: b.status != 'approved')
            record.settlement_amount = sum(approved_bills.mapped('amount'))
            
    @api.depends('bill_settlement_ids.date', 'bill_settlement_ids.status')
    def _compute_settlement_date(self):
        """Compute the latest settlement date from approved bills"""
        for record in self:
            approved_bills = record.bill_settlement_ids.filtered(lambda b: b.status == 'approved')
            if approved_bills:
                record.settlement_date = max(approved_bills.mapped('approval_date'))
            else:
                record.settlement_date = False
                
    @api.depends('bill_settlement_ids.status')
    def _compute_has_pending_bills(self):
        """Check if there are pending bills"""
        for record in self:
            pending_bills = record.bill_settlement_ids.filtered(lambda b: b.status == 'submitted')
            record.has_pending_bills = bool(pending_bills)
    


    def action_approve_selected_bills(self):
        """Action to approve selected bills"""
        self.ensure_one()
        
        if self.state != 'requested':
            raise UserError(_("Bills can only be approved for requests in requested state."))

        pending_bills = self.bill_settlement_ids.filtered(
            lambda b: b.action == 'approve' and b.status == 'submitted'
        )
        
        if not pending_bills:
            raise UserError(_("No bills selected for approval."))
        
        for bill in pending_bills:
            bill.write({
                'status': 'approved',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'action': False,
            })
        
        # Check if all bills are now approved and amounts match
        all_bills_processed = not self.bill_settlement_ids.filtered(lambda b: b.status == 'submitted')
        if all_bills_processed and abs(self.settlement_amount - self.request_amount) < 0.01:
            # All bills approved and amounts match - ready for cash issuing
            self.message_post(
                body=_("All bills approved. Ready for cash issuing."),
                message_type="notification",
            )
        
        self.message_post(
            body=_("Approved %d bills totaling Rs. %.2f") % (
                len(pending_bills), 
                sum(pending_bills.mapped('amount'))
            )
        )
        return True
    
    def action_reject_selected_bills(self):
        """Action to reject selected bills"""
        self.ensure_one()
        
        if self.state != 'requested':
            raise UserError(_("Bills can only be rejected for requests in requested state."))

        pending_bills = self.bill_settlement_ids.filtered(
            lambda b: b.action == 'reject' and b.status == 'submitted'
        )
        
        if not pending_bills:
            raise UserError(_("No bills selected for rejection."))

        bills_without_remarks = pending_bills.filtered(lambda b: not b.rejection_reason)
        
        if bills_without_remarks:
            raise UserError(_("Please provide a rejection reason for all bills you want to reject."))

        for bill in pending_bills:
            if hasattr(bill, 'action_reject'):
                bill.action_reject()
            else:
                bill.write({
                    'status': 'rejected',
                    'rejected_by': self.env.user.id,
                    'rejection_date': fields.Datetime.now(),
                    'action': False,
                })

        self.message_post(
            body=_("Rejected %d bills totaling Rs. %.2f") % (
                len(pending_bills),
                sum(pending_bills.mapped('amount'))
            )
        )
        return True
    
    def action_complete_petty_cash(self):
        """Complete the petty cash request after cash receipt confirmation"""
        self.ensure_one()
        
        if self.state != 'cash_issued':
            raise UserError(_("Only cash issued requests can be completed.")) 
        
        if not self.cashReceivedByEmployee:
            raise UserError(_("Please confirm that employee has received the cash."))
        
        if not self.received_voucher:
            raise UserError(_("Please attach the signed received voucher."))

        self.state = "completed"
        self.message_post(body=_("Petty cash request completed successfully."))
        return True
    
    def action_adjust_request_amount(self):
        """Adjust the request amount based on the approved bills"""
        self.ensure_one()
        
        if self.state != 'requested':
            raise UserError(_("Request must be in Requested state to adjust amount."))
        
        approved_amount = sum(self.bill_settlement_ids.filtered(lambda b: b.status == 'approved').mapped('amount'))

        if approved_amount <= 0:
            raise UserError(_("No approved bills found to adjust the request amount."))
        
        old_amount = self.request_amount
        self.request_amount = approved_amount
        
        self.message_post(
            body=_("Request amount adjusted from Rs. %.2f to Rs. %.2f to match approved bills.") % (old_amount, approved_amount),
            message_type='notification'
        )
        
        return True

    @api.depends('bill_settlement_ids.status')
    def _compute_pending_bills(self):
        """Check if there are pending bills"""
        for record in self:
            pending_bills = record.bill_settlement_ids.filtered(lambda b: b.status in ['draft', 'submitted'])
            record.has_pending_bills = bool(pending_bills)

    @api.depends("request_date")
    def _compute_due_date(self):
        for record in self:
            if record.request_date:
                # Add 10 days to request date (configurable)
                days = int(
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("petty_cash.due_days", 10)
                )
                if isinstance(record.request_date, datetime):
                    record.due_date = record.request_date + timedelta(days=days)
                else:
                    # If request_date is a date, convert to datetime
                    record.due_date = datetime.combine(
                        record.request_date, datetime.min.time()
                    ) + timedelta(days=days)
            else:
                record.due_date = False

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate request number based on request type"""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                if vals.get("request_type") == "iou":
                    # Generate IOU number
                    vals["name"] = self._generate_sequence_number("iou.request")
                else:
                    # Generate Petty Cash number
                    vals["name"] = self._generate_sequence_number("petty.cash.request")
        return super().create(vals_list)

    def _generate_sequence_number(self, sequence_code):
        """Generate sequence number with proper error handling"""
        sequence = self.env["ir.sequence"].next_by_code(sequence_code)
        if not sequence:
            # If sequence doesn't exist, create a temporary one
            year = fields.Date.today().strftime("%y")
            if sequence_code == "iou.request":
                # Find the last IOU number
                last_iou = self.search(
                    [("request_type", "=", "iou")], order="id desc", limit=1
                )
                if last_iou and last_iou.name.startswith("IOU-"):
                    try:
                        last_num = int(last_iou.name.split("-")[-1])
                        return f"IOU-{year}-{str(last_num + 1).zfill(3)}"
                    except:
                        pass
                return f"IOU-{year}-001"
            else:
                # Find the last PC number
                last_pc = self.search(
                    [("request_type", "=", "petty_cash")], order="id desc", limit=1
                )
                if last_pc and last_pc.name.startswith("PC-"):
                    try:
                        last_num = int(last_pc.name.split("-")[-1])
                        return f"PC-{year}-{str(last_num + 1).zfill(3)}"
                    except:
                        pass
                return f"PC-{year}-001"
        return sequence

    @api.onchange("request_type")
    def _onchange_request_type(self):
        """Update the name when request type changes (for new records)"""
        if not self.id and self.name in ["New", "New IOU", "New PC"]:
            if self.request_type == "iou":
                self.name = "New IOU"
            else:
                self.name = "New PC"

    def action_submit(self):
        """Submit petty cash request"""
        if self.state == "draft":
            self.state = "requested"
        return True

    def action_cancel(self):
        """Cancel petty cash request"""
        self.ensure_one()
        if self.state in ["draft", "requested"]:
            self.state = "cancelled"
            self.message_post(body=_("Request cancelled"))
        else:
            raise UserError(
                _("Request can only be cancelled in Draft or Requested state")
            )
        return True

    def action_cash_issued(self):
        """Issue cash - opens denomination popup"""
        self.ensure_one()
        if self.state == "requested":
            
            if not self.bill_settlement_ids:
                raise UserError(_("Please submit bills before issuing cash."))
            
            #check for pending bills
            pending_bills = self.bill_settlement_ids.filtered(lambda b:b.status == 'submitted')
            if pending_bills:
                raise UserError(_("Please approve or reject all bills before issuing cash."))
            
            approved_bills = self.bill_settlement_ids.filtered(lambda b: b.status == 'approved')
            if approved_bills:
                raise UserError(_("No bills have been approved yet."))
            
            if abs(self.settlement_amount - self.request_amount) > 0.01:
                raise UserError(
                    _("Settlement amount (Rs. %.2f) should equal request amount (Rs. %.2f)") % 
                    (self.settlement_amount, self.request_amount)
                )
            # Open denomination popup wizard
            return {
                "name": "Cash Denomination - Petty Cash",
                "type": "ir.actions.act_window",
                "res_model": "cash.denomination.wizard",
                "view_mode": "form",
                "view_id": self.env.ref('petty-cash.cash_denomination_wizard_form').id,
                "target": "new",
                "context": {
                    "default_request_id": self.id,
                    "default_request_amount": self.request_amount,
                    "default_request_type": "petty_cash",
                    "float_request_id": (
                        self.float_request_id.id if self.float_request_id else False
                    ),
                },
            }
        else:
            raise UserError(_("Cash can only be issued for requested petty cash"))

    @api.constrains(
        "request_amount",
        "due_date",
        "request_date",
        "isHodApproved",
        "hodApprovedBy",
        "isFloatManagerApproved",
        "floatManagerApprovedBy",
        "float_request_id",
    )
    def _check_fields(self):
        """Ensure the fields are set correctly"""
        for record in self:
            errors = []
            if record.request_amount <= 0:
                errors.append(
                    _(
                        "Request amount must be greater than zero. Please enter a valid amount."
                    )
                )
            if (
                record.due_date
                and record.request_date
                and record.due_date < record.request_date
            ):
                errors.append(
                    _(
                        "Due date cannot be earlier than request date. Please select a valid due date."
                    )
                )
            if not record.isHodApproved:
                errors.append(_("HOD Approved must be ticked"))
            if record.isHodApproved and not record.hodApprovedBy:
                errors.append(_("Select the approved HOD."))
            if not record.isFloatManagerApproved:
                errors.append(_("Float Manager Approved must be ticked"))
            if record.isFloatManagerApproved and not record.floatManagerApprovedBy:
                errors.append(_("Select the Approved Float Manager."))
            if not record.float_request_id:
                errors.append(_("Please select a float for this petty cash request."))
            if record.request_amount > 5000:
                errors.append(_("Request amount cannot exceed 5000."))
            if errors:
                raise ValidationError("Please fix the following:\n" + "\n".join(errors))

    # @api.constrains()
    # def _check_approval_fields(self):
    #     """Ensure approval fields are set correctly"""
    #     for record in self:
    #         errors = []

    #         if errors:
    #             raise ValidationError('Please fix the following:\n' + '\n'.join(errors))
