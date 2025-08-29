from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError


class FloatRequest(models.Model):
    _name = "float.request"
    _description = "Float Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char(
        string="Float Name",
        required=True,
        tracking=True,
        help="Name of the float request.",
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        required=True,
        tracking=True,
        help="Department this float belongs to",
    )

    initial_amount = fields.Float(
        string="Initial Float Amount",
        required=True,
        tracking=True,
        help="Initial amount allocated for the float request.",
    )

    current_amount = fields.Float(
        string="Current Balance",
        compute="_compute_current_amount",
        store=True,
        help="Current balance of the float request.",
    )

    can_exceed = fields.Boolean(
        string="Can Exceed over the Initial Amount?",
        default=False,
        tracking=True,
    )

    exceed_limit = fields.Float(
        string="Exceed Limit",
        help="Limit for exceeding the initial amount if can_exceed is True.",
        default=0.0,
        tracking=True,
    )

    float_manager_id = fields.Many2one(
        "res.users",
        string="Float Manager",
        required=True,
        default=lambda self: self.env.user,
        help="User responsible for managing this float request.",
    )

    date_created = fields.Date(
        string="Date",
        readonly=True,
        default=fields.Date.today,
        tracking=True,
    )

    remarks = fields.Text(
        string="Remarks",
        help="Additional remarks or notes regarding the float request.",
    )

    attachment = fields.Binary(
        string="Attachment", help="Attachment related to the float request."
    )

    attachment_filename = fields.Char(
        string="Attachment Filename",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    allow_cross_department_request = fields.Boolean(
        string="Allow Cross Department Request?",
        default=False,
        help="Allow employees to request from this float even if from different department",
        tracking=True,
    )

    exceed_margin_percentage = fields.Float(
        string="Exceed Margin %",
        default=10.0,
        help="Percentage margin allowed over the initial amount"
    )

    petty_cash_request_id = fields.One2many(
        "petty.cash.request",
        "float_request_id",
        string="Petty Cash Requests",
    )

    iou_request_id = fields.One2many(
        "petty.cash.iou.request",
        "float_request_id",
        string="IOU Requests",
    )

    total_iou_requests = fields.Integer(
        string="Total IOU Requests",
        compute="_compute_request_totals",
        store=True,
    )

    total_petty_cash_requests = fields.Integer(
        string="Total Petty Cash Requests",
        compute="_compute_request_totals",
        store=True,
    )

    total_requests = fields.Integer(
        string="Total Requests",
        compute="_compute_request_totals",
        store=True,
    )

    cash_in_hand = fields.Float(
        string="Cash in Hand",
        compute="_compute_cash_in_hand",
        store=True,
        help="Available cash for disbursement",
    )

    iou_amount = fields.Float(
        string="IOU Amount",
        compute="_compute_iou_amount",
        store=True,
        help="Total IOU amount requested against this float",
    )

    denomination_ids = fields.One2many(
        "float.denomination",
        "float_request_id",
        string="Denominations",
        help="Denominations used in this float request.",
    )

    current_denomination_id = fields.Many2one(
        "float.denomination",
        string="Current Denomination",
        help="Current denomination used for this float request.",
        compute="_compute_current_denomination",
        store=True,
    )

    reimbursement_ids = fields.One2many(
        "cash.reimbursement",
        "float_request_id",
        string="Cash Reimbursements",
    )
    
    float_customization_ids = fields.One2many(
        "float.customization",
        "float_request_id",
        string="Float Customizations",
        help="Customization requests for this float"
    )

    has_pending_customization = fields.Boolean(
        string="Has Pending Customization Requests?",
        compute="_compute_customization_status",
        help="Check if there are pending customizations for this float"
    )
    
    @api.depends('state')
    def _compute_state_display(self):
        """Compute human-readable state display"""
        for record in self:
            record.state_display = record.state.replace('_', ' ').title()
            
    @api.depends('float_customization_ids.state')
    def _compute_customization_status(self):
        """Check if there are pending customizations"""
        for record in self:
            pending_customizations = record.float_customization_ids.filtered(
                lambda r: r.state in ['draft', 'requested']
            )
            record.has_pending_customization = bool(pending_customizations)

    @api.depends("denomination_ids")
    def _compute_current_denomination(self):
        for record in self:
            if record.denomination_ids:
                # Get the denomination with the latest last_updated timestamp
                latest_denomination = record.denomination_ids.search(
                    [("float_request_id", "=", record.id)],
                    order="last_updated desc",
                    limit=1,
                )

                record.current_denomination_id = (
                    latest_denomination.id if latest_denomination else False
                )
            else:
                record.current_denomination_id = False

    # def create_initial_denomination_record(self):
    #     """Create an initial denomination record for the float request."""
    #     self.ensure_one()
    #     if not self.denomination_ids and self.state == "approved":

    #         intial_amount = self.initial_amount
    #         denom_data = self._calculate_initial_denominations(intial_amount)

    #         self.env["float.denomination"].create(
    #             {"float_request_id": self.id, **denom_data}
    #         )

    # def _calculate_initial_denominations(self, amount):
    #     """Calculate the initial denominations based on the given amount."""

    #     remaining_amount = amount

    #     denom_5000 = min(int(remaining_amount / 5000), 10)  # Max 10 notes of 5000
    #     remaining_amount -= denom_5000 * 5000

    #     denom_1000 = min(int(remaining_amount / 1000), 20)  # Max 20 notes of 1000
    #     remaining_amount -= denom_1000 * 1000

    #     denom_500 = min(int(remaining_amount / 500), 20)
    #     remaining_amount -= denom_500 * 500

    #     denom_100 = min(int(remaining_amount / 100), 50)
    #     remaining_amount -= denom_100 * 100

    #     denom_50 = min(int(remaining_amount / 50), 20)
    #     remaining_amount -= denom_50 * 50

    #     denom_20 = min(int(remaining_amount / 20), 50)
    #     remaining_amount -= denom_20 * 20

    #     denom_10 = min(int(remaining_amount / 10), 100)
    #     remaining_amount -= denom_10 * 10

    #     denom_5 = min(int(remaining_amount / 5), 100)
    #     remaining_amount -= denom_5 * 5

    #     denom_2 = min(int(remaining_amount / 2), 100)
    #     remaining_amount -= denom_2 * 2

    #     denom_1 = int(remaining_amount)

    #     return {
    #         "denom_5000_qty": denom_5000,
    #         "denom_1000_qty": denom_1000,
    #         "denom_500_qty": denom_500,
    #         "denom_100_qty": denom_100,
    #         "denom_50_qty": denom_50,
    #         "denom_20_qty": denom_20,
    #         "denom_10_qty": denom_10,
    #         "denom_5_qty": denom_5,
    #         "denom_2_qty": denom_2,
    #         "denom_1_qty": denom_1,
    #     }

    def action_approve(self):
        """Approve the float request."""
        for record in self:
            if record.state != "requested":
                raise UserError(
                    _('Only requests in "Requested" state can be approved.')
                )
            record.state = "approved"
            record.message_post(
                body=_("Float request approved by %s") % self.env.user.name,
                message_type="notification",
            )

            existing_denomination = self.env["float.denomination"].search(
                [
                    ("float_request_id", "=", record.id),
                ]
            )

            if not existing_denomination:
                return {
                    "type": "ir.actions.act_window",
                    "name": "Setup Initial Denominations",
                    "res_model": "initial.denomination.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": {
                        "default_float_request_id": record.id,
                    },
                }
            else:
                # Denomination already exists, just compute current
                record._compute_current_denomination()

    def action_reject(self):
        """Reject the float request."""
        for record in self:
            if record.state != "requested":
                raise UserError(
                    _('Only requests in "Requested" state can be rejected.')
                )
            record.state = "rejected"
            record.message_post(
                body=_("Float request rejected by %s") % self.env.user.name,
                message_type="notification",
            )
            
    def action_create_customization(self):
        """Create new request"""
        self.ensure_one()
        
        if self.state != 'approved':
            raise UserError(_("Customizations can only be requested for approved float requests."))
        
        if self.has_pending_customization:
            raise UserError(_("There are already pending customization requests for this float."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Customize Float - {self.name}',
            'res_model': 'float.customization', 
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_float_request_id': self.id
            }
        }

    def action_view_customizations(self):
        """Open the customization records for this float"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Customizations - {self.name}",
            "res_model": "float.customization",
            "view_mode": "list,form",
            "domain": [("float_request_id", "=", self.id)],
            "context": {
                "default_float_request_id": self.id,
            },
        }

    def action_setup_denominations(self):
        self.ensure_one()

        if self.state != "approved":
            raise UserError(
                _("Denominations can only be set up for approved float requests.")
            )

        existing_denomination = self.env["float.denomination"].search(
            [("float_request_id", "=", self.id)]
        )

        if existing_denomination:
            raise UserError(
                _("Denominations have already been set up for this float request.")
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Setup Initial Denominations",
            "res_model": "initial.denomination.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_float_request_id": self.id,
            },
        }

    def action_view_denominations(self):
        """Open the denomination records for this float"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Denominations - {self.name}",
            "res_model": "float.denomination",
            "view_mode": "list,form",
            "domain": [("float_request_id", "=", self.id)],
            "context": {
                "default_float_request_id": self.id,
            },
        }

    @api.depends("iou_request_id", "petty_cash_request_id")
    def _compute_request_totals(self):
        for record in self:
            record.total_iou_requests = len(record.iou_request_id)
            record.total_petty_cash_requests = len(record.petty_cash_request_id)
            record.total_requests = (
                record.total_iou_requests + record.total_petty_cash_requests
            )

    @api.depends(
        "initial_amount",
        "petty_cash_request_id.request_amount",
        "petty_cash_request_id.state",
    )
    def _compute_current_amount(self):
        for record in self:
            completed_requests = record.petty_cash_request_id.filtered(
                lambda r: r.state in ["approved", "completed", "cash_issued"]
            )
            disbursed_amount = sum(completed_requests.mapped("request_amount"))
            record.current_amount = record.initial_amount - disbursed_amount

    @api.depends(
        "current_amount", "iou_request_id.state", "iou_request_id.request_amount"
    )
    def _compute_cash_in_hand(self):
        for record in self:
            pending_ious = record.iou_request_id.filtered(
                lambda r: r.state in ["pending_bill_submission", "cash_issued"]
            )
            iou_amount = sum(pending_ious.mapped("request_amount"))
            record.cash_in_hand = record.current_amount - iou_amount

    @api.depends("iou_request_id.request_amount", "iou_request_id.state")
    def _compute_iou_amount(self):
        for record in self:
            pending_ious = record.iou_request_id.filtered(
                lambda r: r.state in ["pending_bill_submission", "cash_issued"]
            )
            record.iou_amount = sum(pending_ious.mapped("request_amount"))

    @api.constrains("initial_amount", "exceed_limit")
    def _check_amounts(self):
        for record in self:
            if record.initial_amount <= 0:
                raise ValidationError(_("Initial amount must be greater than zero."))
            if not record.initial_amount:
                raise ValidationError(_("Initial amount is required."))
            if record.can_exceed and record.exceed_limit <= 0:
                raise ValidationError(
                    _("Exceed limit must be greater than zero when exceed is allowed.")
                )

    def action_submit(self):
        """Submit the float request for approval."""
        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft requests can be submitted."))
            record.state = "requested"
            record.message_post(
                body=_("Float request submitted for approval."),
                message_type="notification",
            )

    # def action_approve(self):
    #     """Approve the float request."""
    #     for record in self:
    #         if record.state != "requested":
    #             raise UserError(
    #                 _('Only requests in "Requested" state can be approved.')
    #             )
    #         record.state = "approved"
    #         record.message_post(
    #             body=_("Float request approved by %s") % self.env.user.name,
    #             message_type="notification",
    #         )

    def reject(self):
        """Reject the float request."""
        for record in self:
            if record.state != "requested":
                raise UserError(
                    _('Only requests in "Requested" state can be rejected.')
                )
            record.state = "rejected"
            record.message_post(
                body=_("Float request rejected by %s") % self.env.user.name,
                message_type="notification",
            )

    def action_reset_to_draft(self):
        """Reset the float request to draft state."""
        for record in self:
            if record.state not in ["rejected", "cancelled"]:
                raise UserError(
                    _("Only rejected or cancelled requests can be reset to draft.")
                )
            record.state = "draft"

    def action_view_petty_cash_requests(self):
        """Open the related petty cash requests."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Petty Cash Requests - {self.name}",
            "res_model": "petty.cash.request",
            "view_mode": "list,form",
            "domain": [("float_request_id", "=", self.id)],
            "context": {
                "default_float_request_id": self.id,
                "default_request_type": "petty_cash",
            },
        }

    def action_view_iou_requests(self):
        """Open the related IOU requests."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"IOU Requests - {self.name}",
            "res_model": "petty.cash.iou.request",
            "view_mode": "list,form",
            "domain": [("float_request_id", "=", self.id)],
            "context": {
                "default_float_request_id": self.id,
            },
        }

    @api.constrains("name", "department_id")
    def _check_name(self):
        for record in self:
            if not record.name or not record.name.strip():
                raise ValidationError(_("Float name is required and cannot be empty."))

            if len(record.name.strip()) < 3:
                raise ValidationError(
                    _("Float name must be at least 3 characters long.")
                )

            if len(record.name) > 100:
                raise ValidationError(_("Float name cannot exceed 100 characters."))

            if record.department_id:

                domain = [
                    ("name", "=", record.name),
                    ("department_id", "=", record.department_id.id),
                    ("state", "!=", "cancelled"),
                ]

                if hasattr(record, "id") and record.id:
                    domain.append(("id", "!=", record.id))

                duplicate = self.env["float.request"].search(domain, limit=1)
                if duplicate:
                    raise ValidationError(
                        _(
                            'A float with the name "%s" already exists for the %s department.'
                        )
                        % (record.name, record.department_id.name)
                    )

    @api.constrains("float_manager_id")
    def _check_float_manager(self):
        """Validate float manager"""
        for record in self:
            if not record.float_manager_id:
                raise ValidationError(_("Float manager is required."))

    def action_request_reimbursement(self):
        """Open the reimbursement wizard for this float request."""
        self.ensure_one()

        if self.state != "approved":
            raise UserError(
                _("Reimbursement can only be requested for approved float requests.")
            )

        return {
            "type": "ir.actions.act_window",
            "name": f"Request Reimbursement - {self.name}",
            "res_model": "cash.reimbursement",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_float_request_id": self.id,
                "default_handler_name": self.env.user.id,
                "default_state": "draft",
            },
        }
