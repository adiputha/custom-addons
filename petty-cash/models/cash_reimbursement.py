from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time



import logging

_logger = logging.getLogger(__name__)


class CashReimbursement(models.Model):
    _name = "cash.reimbursement"
    _description = "Cash Reimbursement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "request_date desc, id desc"

    name = fields.Char(
        string="Reimbursement Number",
        required=True,
        copy=False,
        readonly=True,
        default="New Reimbursement Request",
        tracking=True,
    )

    float_request_id = fields.Many2one(
        "float.request",
        string="Float",
        required=True,
        tracking=True,
        domain="[('state', 'in', ['approved'])]",
        help="Select the float request for which reimbursement is being made.",
    )

    request_date = fields.Datetime(
        string="Request Date",
        required=True,
        readonly=True,
        default=lambda self: fields.Datetime.now(),
        tracking=True,
        help="The date and time when the reimbursement request was made.",
    )

    handler_name = fields.Many2one(
        "res.users",
        string="Handler Name",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )

    current_balance = fields.Float(
        string="Current Balance",
        related="float_request_id.cash_in_hand",
        readonly=True,
        tracking=True,
    )

    required_amount = fields.Float(
        string="Required Amount for Reimbursement",
        required=True,
        tracking=True,
        help="The amount requested for reimbursement.",
    )

    received_amount = fields.Float(
        string="Received Amount",
        tracking=True,
        help="The amount actually received as reimbursement.",
    )

    justification = fields.Text(
        string="Justification",
        required=True,
        tracking=True,
        help="Provide a justification for the reimbursement request.",
    )

    attachment = fields.Binary(
        string="Attachment",
        help="Attach any relevant documents or files related to the reimbursement request.",
    )

    attachment_filename = fields.Char(
        string="Attachment Filename",
    )

    remarks = fields.Text(
        string="Remarks",
        help="Any additional remarks or comments regarding the reimbursement request.",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending Aproval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("completed", "Completed"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    is_manager_approved = fields.Boolean(
        string="Float Manager Approved",
        default=False,
        tracking=True,
    )

    approved_by = fields.Many2one(
        "res.users",
        string="Approved By",
        tracking=True,
        help="User who approved the reimbursement request.",
    )

    approval_date = fields.Datetime(
        string="Approval Date",
        tracking=True,
        help="Date and time when the reimbursement request was approved.",
    )

    cash_received_by_handler = fields.Boolean(
        string="Cash Received by Handler",
        default=False,
        tracking=True,
        help="Indicates if the handler has received the cash for reimbursement.",
    )

    received_voucher = fields.Binary(
        string="Received Voucher",
        help="Attach the received voucher for the reimbursement.",
    )

    received_voucher_filename = fields.Char(
        string="Received Voucher Filename",
    )

    report_from_date = fields.Date(
        string="Report From Date", help="Start date for expense report generation"
    )

    report_to_date = fields.Date(
        string="Report To Date", help="End date for expense report generation"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                vals.get("name", "New Reimbursement Request") == "New Reimbursement Request"
            ):
                vals["name"] = self._generate_sequence_number()
        return super().create(vals_list)

    def _generate_sequence_number(self):
        """Generate a unique sequence number for the reimbursement request."""
        sequence = self.env["ir.sequence"].next_by_code("cash.reimbursement")
        if not sequence:
            year = fields.Date.today().strftime("%Y")
            last_reimb = self.search([], order="id desc", limit=1)
            if last_reimb and last_reimb.name.startswith("CR-"):
                try:
                    last_num = int(last_reimb.name.split("-")[2])
                    return f"CR-{year}-{str(last_num + 1).zfill(3)}"
                except:
                    pass
            return f"CR-{year}-001"
        return sequence

    @api.constrains("required_amount", "received_amount")
    def _check_amounts(self):
        for record in self:
            if record.required_amount <= 0:
                raise ValidationError(_("Required amount must be greater than zero."))
            if record.received_amount < 0:
                raise ValidationError(_("Received amount cannot be negative."))

    def action_submit(self):
        """Submit reimbursement request for approval"""
        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft requests can be submitted."))
            record.state = "pending"
            record.message_post(
                body=_("Reimbursement request submitted for approval."),
                message_type="notification",
            )

    def action_approve(self):
        """Approve the reimbursement request"""
        for record in self:
            if record.state != "pending":
                raise UserError(_("Only pending requests can be approved."))
            record.write(
                {
                    "state": "approved",
                    "is_manager_approved": True,
                    "approved_by": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                }
            )
            record.message_post(
                body=_("Reimbursement request approved by %s.") % self.env.user.name,
                message_type="notification",
            )

    def action_reject(self):
        """Reject the reimbursement request"""
        for record in self:
            if record.state != "pending":
                raise UserError(_("Only pending requests can be rejected."))
            record.state = "rejected"
            record.message_post(
                body=_("Reimbursement request rejected."),
                message_type="notification",
            )

    def action_complete_request(self):
        """Mark the reimbursement request as completed"""
        for record in self:
            if record.state != "approved":
                raise UserError(_("Only approved requests can be marked as completed."))
            if not record.cash_received_by_handler:
                raise UserError(
                    _(
                        "Cash must be received by the handler before completing the request."
                    )
                )
            if not record.received_amount:
                raise UserError(_("Please enter the Received amount."))

            record._update_float_denomination()

            record.state = "completed"
            record.message_post(
                body=_("Reimbursement request completed."),
                message_type="notification",
            )

    def _update_float_denomination(self):
        """Update the float denomination after reimbursement completion"""
        self.ensure_one()

        current_denom = self.env["float.denomination"].search(
            [
                ("float_request_id", "=", self.float_request_id.id),
            ],
            order="last_updated desc",
            limit=1,
        )

        if current_denom:
            if self.received_amount >= 1000:
                current_denom.denom_1000_qty += int(self.received_amount / 1000)
                remaining = self.received_amount % 1000
                if remaining >= 100:
                    current_denom.denom_100_qty += int(remaining / 100)
                    remaining = remaining % 100
                if remaining >= 50:
                    current_denom.denom_50_qty += int(remaining / 50)
                    remaining = remaining % 50
                if remaining >= 20:
                    current_denom.denom_20_qty += int(remaining / 20)
                    remaining = remaining % 20
                if remaining >= 10:
                    current_denom.denom_10_qty += int(remaining / 10)
                    remaining = remaining % 10
                if remaining >= 1:
                    current_denom.denom_1_qty += int(remaining)
            else:
                remaining = self.received_amount
                if remaining >= 100:
                    current_denom.denom_100_qty += int(remaining / 100)
                    remaining = remaining % 100
                if remaining >= 50:
                    current_denom.denom_50_qty += int(remaining / 50)
                    remaining = remaining % 50
                if remaining >= 20:
                    current_denom.denom_20_qty += int(remaining / 20)
                    remaining = remaining % 20
                if remaining >= 10:
                    current_denom.denom_10_qty += int(remaining / 10)
                    remaining = remaining % 10
                if remaining >= 1:
                    current_denom.denom_1_qty += int(remaining)

            current_denom.last_updated = fields.Datetime.now()

    def action_update_denomination(self):
        self.ensure_one()
        if not self.state in ["approved"]:
            raise UserError(_("Only approved requests can update the denomination."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Update Denomination"),
            "res_model": "cash.denomination.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_reimbursement_id": self.id,
                "default_requested_amount": self.required_amount,
                "default_request_type": "reimbursement",
                "float_request_id": self.float_request_id.id,
            },
        }

    def action_reset_to_draft(self):
        """Reset the reimbursement request to draft state"""
        for record in self:
            if record.state not in ["pending"]:
                raise UserError(_("Only pending requests can be reset to draft."))
            record.state = "draft"
            record.write(
                {
                    "is_manager_approved": False,
                    "approved_by": False,
                    "cash_received_by_handler": False,
                    "received_amount": 0.0,
                    "received_voucher": False,
                    "received_voucher_filename": False,
                }
            )

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name} - {record.float_request_id.name}"
            if record.required_amount:
                name += f" (Req: {record.required_amount:,.2f})"
            result.append((record.id, name))
        return result
    
    
    def get_period_expenses(self):
        """Get petty cash expenses for the specified period"""
        if not self.report_from_date or not self.report_to_date:
            return self.env['petty.cash.request']
        
        try:
            from_datetime = f"{self.report_from_date} 00:00:00",
            to_datetime = f"{self.report_to_date} 23:59:59"

            valid_states = ['completed', 'cash_issued']

            expenses = self.env['petty.cash.request'].search([
                ('float_request_id', '=', self.float_request_id.id),
                ('request_date', '>=', from_datetime),
                ('request_date', '<=', to_datetime),
                ('request_amount', '>', 0),
                ('state', 'in', valid_states)
            ], order='request_date desc')
            
            _logger.info(f"Found {len(expenses)} petty cash expenses for period {self.report_from_date} to {self.report_to_date}")
            return expenses

        except Exception as e:
            _logger.error("Error fetching petty cash expenses: %s", e)
            return self.env['petty.cash.request']

    def action_view_reimbursement_report(self):
        """Action to view reimbursement report"""
        self.ensure_one()
        if not self.report_from_date or not self.report_to_date:
            raise UserError(_("Please set both Report From Date and Report To Date."))
    
        try:
            
            petty_cash_expenses = self.get_period_expenses()
        
            from_datetime = f"{self.report_from_date} 00:00:00"
            to_datetime = f"{self.report_to_date} 23:59:59"

            iou_requests = self.env['petty.cash.iou.request'].search([
                ('float_request_id', '=', self.float_request_id.id),
                ('request_date', '>=', from_datetime),
                ('request_date', '<=', to_datetime),
                ('state', 'in', ['completed', 'pending_bill_submission'])
            ], order='request_date desc')

            
            petty_cash_data = []
            for expense in petty_cash_expenses:
                try:
                    petty_cash_data.append({
                        'name': str(expense.name) if expense.name else 'N/A',
                        'request_by_name': expense.request_by.name if expense.request_by else 'Unknown',
                        'department_name': expense.request_by.department_id.name if expense.request_by and expense.request_by.department_id else 'N/A',
                        'category_name': expense.category.name if expense.category else 'General',
                        'request_amount': float(expense.request_amount) if expense.request_amount else 0.0,
                        'request_date': expense.request_date.strftime('%Y-%m-%d') if expense.request_date else 'N/A',
                        'has_voucher': bool(expense.request_voucher),
                        'state': expense.state.replace('_', ' ').title() if expense.state else 'Unknown',
                        'approved_by_name': expense.hodApprovedBy.name if expense.hodApprovedBy else 'N/A',
                        'has_received_voucher': bool(expense.received_voucher),
                    })
                except Exception as e:
                    _logger.error(f"Error processing expense {expense.id}: {e}")
                    
                    petty_cash_data.append({
                        'name': 'Error',
                        'request_by_name': 'Error',
                        'department_name': 'N/A',
                        'category_name': 'General',
                        'request_amount': 0.0,
                        'request_date': 'N/A',
                        'has_voucher': False,
                        'state': 'Error',
                        'approved_by_name': 'N/A',
                        'has_received_voucher': False,
                    })

            iou_data = []
            for iou in iou_requests:
                try:
                    iou_data.append({
                        'name': str(iou.name) if iou.name else 'N/A',
                        'request_by_name': iou.request_by.name if iou.request_by else 'Unknown',
                        'department_name': iou.request_by.department_id.name if iou.request_by and iou.request_by.department_id else 'N/A',
                        'request_amount': float(iou.request_amount) if iou.request_amount else 0.0,
                        'request_date': iou.request_date.strftime('%Y-%m-%d') if iou.request_date else 'N/A',
                        'due_date': iou.due_date.strftime('%Y-%m-%d') if iou.due_date else 'N/A',
                        'has_voucher': bool(iou.request_voucher),
                        'state': iou.state.replace('_', ' ').title() if iou.state else 'Unknown',
                        'approved_by_name': iou.hodApprovedBy.name if iou.hodApprovedBy else 'N/A',
                    })
                except Exception as e:
                    _logger.error(f"Error processing IOU {iou.id}: {e}")
                    iou_data.append({
                        'name': 'Error',
                        'request_by_name': 'Error',
                        'department_name': 'N/A',
                        'request_amount': 0.0,
                        'request_date': 'N/A',
                        'due_date': 'N/A',
                        'has_voucher': False,
                        'state': 'Error',
                        'approved_by_name': 'N/A',
                    })
                    
            reimbursement_data = {
                'name': str(self.name) if self.name else 'N/A',
                'float_name': self.float_request_id.name if self.float_request_id else 'N/A',
                'handler_name': self.handler_name.name if self.handler_name else 'N/A',
                'total_float_amount': float(self.float_request_id.initial_amount) if self.float_request_id and self.float_request_id.cash_in_hand else 0.0,
                'required_amount': float(self.required_amount) if self.required_amount else 0.0,
                'current_balance': float(self.current_balance) if self.current_balance else 0.0,
                'remarks': str(self.remarks) if self.remarks else 'Monthly Refill',
                'justification': str(self.justification) if self.justification else '',
                'report_from_date': self.report_from_date.strftime('%Y-%m-%d') if self.report_from_date else 'N/A',
                'report_to_date': self.report_to_date.strftime('%Y-%m-%d') if self.report_to_date else 'N/A',
            }
            
            petty_cash_total = sum(item['request_amount'] for item in petty_cash_data)
            iou_total = sum(item['request_amount'] for item in iou_data)

            data = {
                'from_date': self.report_from_date.strftime('%Y-%m-%d'),
                'to_date': self.report_to_date.strftime('%Y-%m-%d'),
                'petty_cash_total': petty_cash_total,
                'iou_total': iou_total,
                'grand_total': petty_cash_total + iou_total
            }
            
        
            context = dict(
                self.env.context,
                petty_cash_data=petty_cash_data,
                iou_data=iou_data,
                report_summary=data,
                reimbursement_info=reimbursement_data,
            )
            
            _logger.info(f"Generating reimbursement report for {self.name} from {self.report_from_date} to {self.report_to_date}")
            _logger.info(f"report dates - From {self.report_from_date} to {self.report_to_date}")

            return self.with_context(context).env.ref('petty-cash.action_reimbursement_report')\
                    .report_action(self, data=data)
                   
        except Exception as e:
            _logger.error(f"Error generating reimbursement report: {e}")
            import traceback
            _logger.error(traceback.format_exc())
            raise UserError(_("Error generating report. Please check the logs and try again."))