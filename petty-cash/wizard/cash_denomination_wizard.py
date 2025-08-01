from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CashDenominationWizard(models.TransientModel):
    _name = "cash.denomination.wizard"
    _description = "Cash Denomination Wizard"

    request_id = fields.Many2one(
        "petty.cash.request",
        string="Petty Cash Request",
        readonly=True,
    )

    iou_request_id = fields.Many2one(
        "petty.cash.iou.request",
        string="IOU Request",
        readonly=True,
    )

    request_number = fields.Char(
        string="Request Number",
        readonly=True,
        compute="_compute_request_details",
        store=True,
        help="The number of the petty cash or IOU request associated with this denomination.",
    )

    requested_amount = fields.Float(
        string="Request Amount",
        readonly=True,
        compute="_compute_request_details",
        store=True,
        help="The amount requested in the petty cash or IOU request.",
    )

    request_type = fields.Selection(
        [("petty_cash", "Petty Cash"), ("iou", "IOU")],
        string="Request Type",
        readonly=True,
        compute="_compute_request_details",
        store=True,
        help="The type of request associated with this denomination (Petty Cash or IOU).",
    )

    selected_amount = fields.Float(
        string="Selected Amount",
        compute="_compute_selected_amount",
        store=True,
    )

    cash_in_hand = fields.Float(
        string="Cash in Hand",
        compute="_compute_cash_in_hand",
        help="The total cash available in hand for denomination.",
        readonly=True,
        store=True,
    )

    is_cash_balanced = fields.Boolean(
        string="Is Cash Balanced",
        default=False,
    )

    balance_amount = fields.Float(
        string="Balance Amount",
        compute="_compute_balance_amount",
        store=True,
    )

    # Denomination fields
    denom_5000_qty = fields.Integer(string="Rs. 5,000 Quantity", default=0)
    denom_1000_qty = fields.Integer(string="Rs. 1,000 Quantity", default=0)
    denom_500_qty = fields.Integer(string="Rs. 500 Quantity", default=0)
    denom_100_qty = fields.Integer(string="Rs. 100 Quantity", default=0)
    denom_50_qty = fields.Integer(string="Rs. 50 Quantity", default=0)
    denom_20_qty = fields.Integer(string="Rs. 20 Quantity", default=0)
    denom_10_qty = fields.Integer(string="Rs. 10 Quantity", default=0)
    denom_5_qty = fields.Integer(string="Rs. 5 Quantity", default=0)
    denom_2_qty = fields.Integer(string="Rs. 2 Quantity", default=0)
    denom_1_qty = fields.Integer(string="Rs. 1 Quantity", default=0)

    # Available denomination quantities (in hand)
    denom_5000_available = fields.Integer(
        string="Rs. 5,000 Available",
        compute="_compute_available_denominations",
        store=True,
    )
    denom_1000_available = fields.Integer(
        string="Rs. 1,000 Available",
        compute="_compute_available_denominations",
        store=True,
    )
    denom_500_available = fields.Integer(
        string="Rs. 500 Available",
        compute="_compute_available_denominations",
        store=True,
    )
    denom_100_available = fields.Integer(
        string="Rs. 100 Available",
        compute="_compute_available_denominations",
        store=True,
    )
    denom_50_available = fields.Integer(
        string="Rs. 50 Available",
        compute="_compute_available_denominations",
        store=True,
    )
    denom_20_available = fields.Integer(
        string="Rs. 20 Available",
        compute="_compute_available_denominations",
        store=True,
    )
    denom_10_available = fields.Integer(
        string="Rs. 10 Available",
        compute="_compute_available_denominations",
        store=True,
    )
    denom_5_available = fields.Integer(
        string="Rs. 5 Available", compute="_compute_available_denominations", store=True
    )
    denom_2_available = fields.Integer(
        string="Rs. 2 Available", compute="_compute_available_denominations", store=True
    )
    denom_1_available = fields.Integer(
        string="Rs. 1 Available", compute="_compute_available_denominations", store=True
    )

    # Balance denomination fields (shown when is_cash_balanced is True)
    balance_5000_qty = fields.Integer(string="Balance Rs. 5,000", default=0)
    balance_1000_qty = fields.Integer(string="Balance Rs. 1,000", default=0)
    balance_500_qty = fields.Integer(string="Balance Rs. 500", default=0)
    balance_100_qty = fields.Integer(string="Balance Rs. 100", default=0)
    balance_50_qty = fields.Integer(string="Balance Rs. 50", default=0)
    balance_20_qty = fields.Integer(string="Balance Rs. 20", default=0)
    balance_10_qty = fields.Integer(string="Balance Rs. 10", default=0)
    balance_5_qty = fields.Integer(string="Balance Rs. 5", default=0)
    balance_2_qty = fields.Integer(string="Balance Rs. 2", default=0)
    balance_1_qty = fields.Integer(string="Balance Rs. 1", default=0)

    selected_balance_amount = fields.Float(
        string="Selected Balance Amount",
        compute="_compute_selected_balance_amount",
        store=True,
    )

    @api.depends("request_id", "iou_request_id")
    def _compute_request_details(self):
        for record in self:
            if record.request_id:
                record.request_number = record.request_id.name
                record.requested_amount = record.request_id.request_amount
                record.request_type = "petty_cash"
            elif record.iou_request_id:
                record.request_number = record.iou_request_id.name
                record.requested_amount = record.iou_request_id.request_amount
                record.request_type = "iou"
            else:
                record.request_number = ""
                record.requested_amount = 0.0
                record.request_type = False

    @api.depends("request_id", "iou_request_id")
    def _compute_available_denominations(self):
        for record in self:
            float_request = None
            if record.request_id:
                float_request = record.request_id.float_request_id
            elif record.iou_request_id:
                float_request = record.iou_request_id.float_request_id

            if float_request and float_request.current_denomination_id:
                # Get current denomination from the float
                current_denom = float_request.current_denomination_id
                record.denom_5000_available = current_denom.denom_5000_qty
                record.denom_1000_available = current_denom.denom_1000_qty
                record.denom_500_available = current_denom.denom_500_qty
                record.denom_100_available = current_denom.denom_100_qty
                record.denom_50_available = current_denom.denom_50_qty
                record.denom_20_available = current_denom.denom_20_qty
                record.denom_10_available = current_denom.denom_10_qty
                record.denom_5_available = current_denom.denom_5_qty
                record.denom_2_available = current_denom.denom_2_qty
                record.denom_1_available = current_denom.denom_1_qty
            else:
                # Set all to 0 if no denomination found
                record.denom_5000_available = 0
                record.denom_1000_available = 0
                record.denom_500_available = 0
                record.denom_100_available = 0
                record.denom_50_available = 0
                record.denom_20_available = 0
                record.denom_10_available = 0
                record.denom_5_available = 0
                record.denom_2_available = 0
                record.denom_1_available = 0

    @api.depends("request_id", "iou_request_id")
    def _compute_cash_in_hand(self):
        for record in self:
            float_request = None
            if record.request_id:
                float_request = record.request_id.float_request_id
            elif record.iou_request_id:
                float_request = record.iou_request_id.float_request_id

            if float_request:
                record.cash_in_hand = float_request.cash_in_hand
            else:
                record.cash_in_hand = 0.0

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        if self.env.context.get("default_request_id"):
            request_id = self.env.context.get("default_request_id")
            defaults["request_id"] = request_id

            request = self.env["petty.cash.request"].browse(request_id)
            if request.exists():
                defaults["request_number"] = request.name
                defaults["requested_amount"] = request.request_amount

        elif self.env.context.get("default_iou_request_id"):
            iou_request_id = self.env.context.get("default_iou_request_id")
            defaults["iou_request_id"] = iou_request_id

            iou_request = self.env["petty.cash.iou.request"].browse(iou_request_id)
            if iou_request.exists():
                defaults["request_number"] = iou_request.name
                defaults["requested_amount"] = iou_request.request_amount

        return defaults

    @api.depends(
        "denom_5000_qty",
        "denom_1000_qty",
        "denom_500_qty",
        "denom_100_qty",
        "denom_50_qty",
        "denom_20_qty",
        "denom_10_qty",
        "denom_5_qty",
        "denom_2_qty",
        "denom_1_qty",
    )
    def _compute_selected_amount(self):
        for record in self:
            amount = (
                record.denom_5000_qty * 5000
                + record.denom_1000_qty * 1000
                + record.denom_500_qty * 500
                + record.denom_100_qty * 100
                + record.denom_50_qty * 50
                + record.denom_20_qty * 20
                + record.denom_10_qty * 10
                + record.denom_5_qty * 5
                + record.denom_2_qty * 2
                + record.denom_1_qty * 1
            )
            record.selected_amount = amount

    @api.depends("selected_amount", "requested_amount")
    def _compute_balance_amount(self):
        for record in self:
            record.balance_amount = record.requested_amount - record.selected_amount

    @api.depends(
        "balance_5000_qty",
        "balance_1000_qty",
        "balance_500_qty",
        "balance_100_qty",
        "balance_50_qty",
        "balance_20_qty",
        "balance_10_qty",
        "balance_5_qty",
        "balance_2_qty",
        "balance_1_qty",
    )
    def _compute_selected_balance_amount(self):
        for record in self:
            amount = (
                record.balance_5000_qty * 5000
                + record.balance_1000_qty * 1000
                + record.balance_500_qty * 500
                + record.balance_100_qty * 100
                + record.balance_50_qty * 50
                + record.balance_20_qty * 20
                + record.balance_10_qty * 10
                + record.balance_5_qty * 5
                + record.balance_2_qty * 2
                + record.balance_1_qty * 1
            )
            record.selected_balance_amount = amount

    @api.constrains(
        "denom_5000_qty",
        "denom_1000_qty",
        "denom_500_qty",
        "denom_100_qty",
        "denom_50_qty",
        "denom_20_qty",
        "denom_10_qty",
        "denom_5_qty",
        "denom_2_qty",
        "denom_1_qty",
    )
    def _check_available_denominations(self):
        for record in self:
            if record.denom_5000_qty > record.denom_5000_available:
                raise UserError(_("Not enough Rs. 5,000 notes available"))
            if record.denom_1000_qty > record.denom_1000_available:
                raise UserError(_("Not enough Rs. 1,000 notes available"))
            if record.denom_500_qty > record.denom_500_available:
                raise UserError(_("Not enough Rs. 500 notes available"))
            if record.denom_100_qty > record.denom_100_available:
                raise UserError(_("Not enough Rs. 100 notes available"))
            if record.denom_50_qty > record.denom_50_available:
                raise UserError(_("Not enough Rs. 50 notes available"))
            if record.denom_20_qty > record.denom_20_available:
                raise UserError(_("Not enough Rs. 20 notes available"))
            if record.denom_10_qty > record.denom_10_available:
                raise UserError(_("Not enough Rs. 10 notes available"))
            if record.denom_5_qty > record.denom_5_available:
                raise UserError(_("Not enough Rs. 5 coins available"))
            if record.denom_2_qty > record.denom_2_available:
                raise UserError(_("Not enough Rs. 2 coins available"))
            if record.denom_1_qty > record.denom_1_available:
                raise UserError(_("Not enough Rs. 1 coins available"))

    def action_update_amount(self):
        """Update the denomination and process the request"""
        self.ensure_one()

        # Validate selected amount
        if self.is_cash_balanced:
            expected_amount = self.requested_amount + self.selected_balance_amount
            if abs(self.selected_amount - expected_amount) > 0.01:
                raise UserError(
                    _("Selected amount does not match the expected amount.")
                )
        else:
            if abs(self.selected_amount - self.requested_amount) > 0.01:
                raise UserError(
                    _("Selected amount does not match the requested amount.")
                )

        # Get float request and current denomination
        float_request = None
        if self.request_id:
            float_request = self.request_id.float_request_id
        elif self.iou_request_id:
            float_request = self.iou_request_id.float_request_id

        if not float_request:
            raise UserError(_("No float request found."))

        # Update denomination in float
        if float_request.current_denomination_id:
            current_denom = float_request.current_denomination_id

            # Create dictionary of denominations used
            denomination_used = {
                "denom_5000_qty": self.denom_5000_qty,
                "denom_1000_qty": self.denom_1000_qty,
                "denom_500_qty": self.denom_500_qty,
                "denom_100_qty": self.denom_100_qty,
                "denom_50_qty": self.denom_50_qty,
                "denom_20_qty": self.denom_20_qty,
                "denom_10_qty": self.denom_10_qty,
                "denom_5_qty": self.denom_5_qty,
                "denom_2_qty": self.denom_2_qty,
                "denom_1_qty": self.denom_1_qty,
            }

            # Update the denomination record
            current_denom.update_denomination_after_reimbursement(denomination_used)

        # Create denomination details message
        denomination_details = self._create_denomination_message()

        # Update request state and add message
        if self.request_id:
            self.request_id.state = "cash_issued"
            self.request_id.message_post(body=denomination_details)
        elif self.iou_request_id:
            self.iou_request_id.state = "pending_bill_submission"
            self.iou_request_id.cashReceivedByEmployee = True
            self.iou_request_id.message_post(body=denomination_details)

        return {
            "type": "ir.actions.act_window_close",
        }

    def _create_denomination_message(self):
        """Create a detailed message showing denomination breakdown"""
        message = f"""
        <h4>💰 Cash Issued Details:</h4>
        <table class="table table-sm">
            <thead>
                <tr><th>Denomination</th><th>Quantity</th><th>Amount</th></tr>
            </thead>
            <tbody>
        """

        denominations = [
            (5000, self.denom_5000_qty, "Rs. 5,000"),
            (1000, self.denom_1000_qty, "Rs. 1,000"),
            (500, self.denom_500_qty, "Rs. 500"),
            (100, self.denom_100_qty, "Rs. 100"),
            (50, self.denom_50_qty, "Rs. 50"),
            (20, self.denom_20_qty, "Rs. 20"),
            (10, self.denom_10_qty, "Rs. 10"),
            (5, self.denom_5_qty, "Rs. 5"),
            (2, self.denom_2_qty, "Rs. 2"),
            (1, self.denom_1_qty, "Rs. 1"),
        ]

        for value, qty, label in denominations:
            if qty > 0:
                amount = value * qty
                message += f"""
                <tr>
                    <td>{label}</td>
                    <td>{qty}</td>
                    <td>Rs. {amount:,.2f}</td>
                </tr>
                """

        message += f"""
            </tbody>
            <tfoot>
                <tr><th>Total Cash Issued:</th><th></th><th>Rs. {self.selected_amount:,.2f}</th></tr>
            </tfoot>
        </table>
        """

        if self.is_cash_balanced:
            message += f"""
            <div class="alert alert-info">
                <strong>Balance Given:</strong> Rs. {self.selected_balance_amount:,.2f}
            </div>
            """

        return message

    def action_auto_calculate(self):
        """Auto-calculate denomination breakdown based on requested amount"""
        self.ensure_one()

        amount = self.requested_amount
        if amount <= 0:
            raise UserError(_("No amount to calculate denominations for."))

        # Get available denominations
        available_denoms = {
            5000: self.denom_5000_available,
            1000: self.denom_1000_available,
            500: self.denom_500_available,
            100: self.denom_100_available,
            50: self.denom_50_available,
            20: self.denom_20_available,
            10: self.denom_10_available,
            5: self.denom_5_available,
            2: self.denom_2_available,
            1: self.denom_1_available,
        }

        # Calculate optimal breakdown
        remaining = amount
        breakdown = {}

        for value in sorted(available_denoms.keys(), reverse=True):
            if remaining <= 0:
                break

            max_available = available_denoms[value]
            needed = min(int(remaining / value), max_available)
            breakdown[value] = needed
            remaining -= needed * value

        # Update fields
        self.denom_5000_qty = breakdown.get(5000, 0)
        self.denom_1000_qty = breakdown.get(1000, 0)
        self.denom_500_qty = breakdown.get(500, 0)
        self.denom_100_qty = breakdown.get(100, 0)
        self.denom_50_qty = breakdown.get(50, 0)
        self.denom_20_qty = breakdown.get(20, 0)
        self.denom_10_qty = breakdown.get(10, 0)
        self.denom_5_qty = breakdown.get(5, 0)
        self.denom_2_qty = breakdown.get(2, 0)
        self.denom_1_qty = breakdown.get(1, 0)

        if remaining > 0:
            raise UserError(
                _(
                    "Cannot fulfill the full amount. Remaining Rs. %.2f cannot be provided with available denominations."
                )
                % remaining
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Auto-calculated"),
                "message": _(
                    "Denomination breakdown has been automatically calculated."
                ),
                "type": "success",
            },
        }

    def action_cancel(self):
        """Cancel the cash denomination wizard"""
        return {
            "type": "ir.actions.act_window_close",
        }
