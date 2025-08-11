from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


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
    )

    requested_amount = fields.Float(
        string="Request Amount",
        readonly=True,
    )

    request_type = fields.Selection(
        [
            ("petty_cash", "Petty Cash"),
            ("iou", "IOU"),
            ("reimbursement", "Reimbursement"),
        ],
        string="Request Type",
        readonly=True,
    )

    selected_amount = fields.Float(
        string="Selected Amount",
        compute="_compute_selected_amount",
    )

    cash_in_hand = fields.Float(
        string="Cash in Hand",
        readonly=True,
    )

    is_cash_balanced = fields.Boolean(
        string="Is Cash Balanced",
        default=False,
    )

    balance_amount = fields.Float(
        string="Balance Amount",
        compute="_compute_balance_amount",
    )

    amount_difference = fields.Float(
        string="Amount Difference",
        compute="_compute_amount_difference",
    )

    is_amount_matched = fields.Boolean(
        string="Is Amount Matched",
        compute="_compute_amount_difference",
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

    # Available denomination quantities - Regular fields, not computed
    denom_5000_available = fields.Integer(
        string="Rs. 5,000 Available", readonly=True, default=0
    )
    denom_1000_available = fields.Integer(
        string="Rs. 1,000 Available", readonly=True, default=0
    )
    denom_500_available = fields.Integer(
        string="Rs. 500 Available", readonly=True, default=0
    )
    denom_100_available = fields.Integer(
        string="Rs. 100 Available", readonly=True, default=0
    )
    denom_50_available = fields.Integer(
        string="Rs. 50 Available", readonly=True, default=0
    )
    denom_20_available = fields.Integer(
        string="Rs. 20 Available", readonly=True, default=0
    )
    denom_10_available = fields.Integer(
        string="Rs. 10 Available", readonly=True, default=0
    )
    denom_5_available = fields.Integer(
        string="Rs. 5 Available", readonly=True, default=0
    )
    denom_2_available = fields.Integer(
        string="Rs. 2 Available", readonly=True, default=0
    )
    denom_1_available = fields.Integer(
        string="Rs. 1 Available", readonly=True, default=0
    )

    # Balance denomination fields
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

    balance_5000_available = fields.Integer(
        string="Balance Rs. 5,000 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_1000_available = fields.Integer(
        string="Balance Rs. 1,000 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_500_available = fields.Integer(
        string="Balance Rs. 500 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_100_available = fields.Integer(
        string="Balance Rs. 100 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_50_available = fields.Integer(
        string="Balance Rs. 50 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_20_available = fields.Integer(
        string="Balance Rs. 20 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_10_available = fields.Integer(
        string="Balance Rs. 10 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_5_available = fields.Integer(
        string="Balance Rs. 5 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_2_available = fields.Integer(
        string="Balance Rs. 2 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )
    balance_1_available = fields.Integer(
        string="Balance Rs. 1 Available",
        readonly=True,
        default=0,
        compute="_compute_balance_available",
        store=True,
    )

    selected_balance_amount = fields.Float(
        string="Selected Balance Amount",
        compute="_compute_selected_balance_amount",
    )

    reimbursement_id = fields.Many2one(
        "cash.reimbursement",
        string="Reimbursement Request",
        readonly=True,
    )

    @api.depends("selected_amount", "requested_amount")
    def _compute_amount_difference(self):
        for record in self:
            difference = abs(record.selected_amount - record.requested_amount)
            record.amount_difference = difference
            record.is_amount_matched = difference < 0.01

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
            record.balance_amount = record.selected_amount - record.requested_amount

    @api.depends(
        "denom_5000_available",
        "denom_5000_qty",
        "denom_1000_available",
        "denom_1000_qty",
        "denom_500_available",
        "denom_500_qty",
        "denom_100_available",
        "denom_100_qty",
        "denom_50_available",
        "denom_50_qty",
        "denom_20_available",
        "denom_20_qty",
        "denom_10_available",
        "denom_10_qty",
        "denom_5_available",
        "denom_5_qty",
        "denom_2_available",
        "denom_2_qty",
        "denom_1_available",
        "denom_1_qty",
    )
    def _compute_balance_available(self):
        """Compute available balance denominations after main selection"""
        for record in self:
            record.balance_5000_available = max(
                0, record.denom_5000_available - record.denom_5000_qty
            )
            record.balance_1000_available = max(
                0, record.denom_1000_available - record.denom_1000_qty
            )
            record.balance_500_available = max(
                0, record.denom_500_available - record.denom_500_qty
            )
            record.balance_100_available = max(
                0, record.denom_100_available - record.denom_100_qty
            )
            record.balance_50_available = max(
                0, record.denom_50_available - record.denom_50_qty
            )
            record.balance_20_available = max(
                0, record.denom_20_available - record.denom_20_qty
            )
            record.balance_10_available = max(
                0, record.denom_10_available - record.denom_10_qty
            )
            record.balance_5_available = max(
                0, record.denom_5_available - record.denom_5_qty
            )
            record.balance_2_available = max(
                0, record.denom_2_available - record.denom_2_qty
            )
            record.balance_1_available = max(
                0, record.denom_1_available - record.denom_1_qty
            )

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

    @api.model
    def default_get(self, fields_list):
        """Set default values including available denominations"""
        defaults = super().default_get(fields_list)

        _logger.info(f"Context in default_get: {self.env.context}")
        _logger.info(f"Fields requested: {fields_list}")

        try:
            if self.env.context.get("default_request_id"):
                request_id = self.env.context.get("default_request_id")
                defaults["request_id"] = request_id

                request = self.env["petty.cash.request"].browse(request_id)
                if request.exists():
                    defaults["request_number"] = request.name
                    defaults["requested_amount"] = request.request_amount
                    defaults["request_type"] = "petty_cash"

                    # Load float and denomination data
                    float_request = request.float_request_id
                    if float_request:
                        defaults["cash_in_hand"] = float_request.cash_in_hand

                        # Load available denominations
                        denom_data = self._get_denomination_data(float_request)
                        defaults.update(denom_data)

                        _logger.info(f"Loaded denomination data: {denom_data}")

            elif self.env.context.get("default_iou_request_id"):
                iou_request_id = self.env.context.get("default_iou_request_id")
                defaults["iou_request_id"] = iou_request_id

                iou_request = self.env["petty.cash.iou.request"].browse(iou_request_id)
                if iou_request.exists():
                    defaults["request_number"] = iou_request.name
                    defaults["requested_amount"] = iou_request.request_amount
                    defaults["request_type"] = "iou"

                    # Load float and denomination data
                    float_request = iou_request.float_request_id
                    if float_request:
                        defaults["cash_in_hand"] = float_request.cash_in_hand

                        # Load available denominations
                        denom_data = self._get_denomination_data(float_request)
                        defaults.update(denom_data)

            elif self.env.context.get("default_reimbursement_id"):
                reimbursement_id = self.env.context.get("default_reimbursement_id")
                defaults["reimbursement_id"] = reimbursement_id

                reimbursement = self.env["petty.cash.reimbursement"].browse(
                    reimbursement_id
                )
                if reimbursement.exists():
                    defaults["request_number"] = reimbursement.name
                    defaults["requested_amount"] = reimbursement.required_amount
                    defaults["request_type"] = "reimbursement"

                    # Load float and denomination data
                    float_request = reimbursement.float_request_id
                    if float_request:
                        defaults["cash_in_hand"] = float_request.cash_in_hand

                        # Load available denominations
                        denom_data = self._get_denomination_data(float_request)
                        defaults.update(denom_data)

                        _logger.info(f"Loaded denomination data: {denom_data}")

        except Exception as e:
            _logger.error(f"Error in default_get: {e}")
            # Set default values to prevent errors
            defaults.update(
                {
                    "request_number": "",
                    "requested_amount": 0.0,
                    "cash_in_hand": 0.0,
                    "denom_5000_available": 0,
                    "denom_1000_available": 0,
                    "denom_500_available": 0,
                    "denom_100_available": 0,
                    "denom_50_available": 0,
                    "denom_20_available": 0,
                    "denom_10_available": 0,
                    "denom_5_available": 0,
                    "denom_2_available": 0,
                    "denom_1_available": 0,
                }
            )

        return defaults

    def _get_denomination_data(self, float_request):
        """Get denomination data from float request"""
        # Search for the latest denomination record
        current_denom = self.env["float.denomination"].search(
            [("float_request_id", "=", float_request.id)],
            order="last_updated desc",
            limit=1,
        )

        if current_denom:
            _logger.info(
                f"Found denomination record: {current_denom.id} with total: {current_denom.total_amount}"
            )
            return {
                "denom_5000_available": current_denom.denom_5000_qty,
                "denom_1000_available": current_denom.denom_1000_qty,
                "denom_500_available": current_denom.denom_500_qty,
                "denom_100_available": current_denom.denom_100_qty,
                "denom_50_available": current_denom.denom_50_qty,
                "denom_20_available": current_denom.denom_20_qty,
                "denom_10_available": current_denom.denom_10_qty,
                "denom_5_available": current_denom.denom_5_qty,
                "denom_2_available": current_denom.denom_2_qty,
                "denom_1_available": current_denom.denom_1_qty,
            }
        else:
            _logger.warning(
                f"No denomination record found for float: {float_request.name}"
            )
            return {
                "denom_5000_available": 0,
                "denom_1000_available": 0,
                "denom_500_available": 0,
                "denom_100_available": 0,
                "denom_50_available": 0,
                "denom_20_available": 0,
                "denom_10_available": 0,
                "denom_5_available": 0,
                "denom_2_available": 0,
                "denom_1_available": 0,
            }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure proper initialization"""
        records = super().create(vals_list)

        for record in records:
            # If denominations weren't loaded in default_get, load them now
            if hasattr(record, "request_id") or hasattr(record, "iou_request_id"):
                if all(
                    getattr(record, f"denom_{d}_available", 0) == 0
                    for d in [
                        "5000",
                        "1000",
                        "500",
                        "100",
                        "50",
                        "20",
                        "10",
                        "5",
                        "2",
                        "1",
                    ]
                ):
                    record._load_denominations()

        return records

    def _load_denominations(self):
        """Load denominations for the current record"""
        self.ensure_one()

        float_request = None
        if self.request_id:
            float_request = self.request_id.float_request_id
            if not self.request_number:
                self.request_number = self.request_id.name
                self.requested_amount = self.request_id.request_amount
                self.request_type = "petty_cash"
        elif self.iou_request_id:
            float_request = self.iou_request_id.float_request_id
            if not self.request_number:
                self.request_number = self.iou_request_id.name
                self.requested_amount = self.iou_request_id.request_amount
                self.request_type = "iou"

        if float_request:
            self.cash_in_hand = float_request.cash_in_hand
            denom_data = self._get_denomination_data(float_request)

            # Update the record with denomination data
            for field, value in denom_data.items():
                setattr(self, field, value)

            _logger.info(f"Loaded denominations for record {self.id}")

    def refresh_available_amounts(self):
        """Refresh available denominations"""
        self.ensure_one()
        self._load_denominations()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Refreshed"),
                "message": _("Available denominations refreshed successfully."),
                "type": "success",
            },
        }

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
            errors = []

            checks = [
                (record.denom_5000_qty, record.denom_5000_available, "Rs. 5,000"),
                (record.denom_1000_qty, record.denom_1000_available, "Rs. 1,000"),
                (record.denom_500_qty, record.denom_500_available, "Rs. 500"),
                (record.denom_100_qty, record.denom_100_available, "Rs. 100"),
                (record.denom_50_qty, record.denom_50_available, "Rs. 50"),
                (record.denom_20_qty, record.denom_20_available, "Rs. 20"),
                (record.denom_10_qty, record.denom_10_available, "Rs. 10"),
                (record.denom_5_qty, record.denom_5_available, "Rs. 5"),
                (record.denom_2_qty, record.denom_2_available, "Rs. 2"),
                (record.denom_1_qty, record.denom_1_available, "Rs. 1"),
            ]

            for needed, available, denomination in checks:
                if needed > available:
                    errors.append(
                        f"{denomination}: Need {needed}, Available {available}"
                    )

            if errors:
                error_msg = _("Not enough denominations available:\n") + "\n".join(
                    errors
                )
                raise UserError(error_msg)

    @api.constrains(
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
    def _check_balance_denominations(self):
        for record in self:
            if not record.is_cash_balanced:
                continue
            errors = []
            checks = [
                (record.balance_5000_qty, record.denom_5000_available, "Rs. 5,000"),
                (record.balance_1000_qty, record.denom_1000_available, "Rs. 1,000"),
                (record.balance_500_qty, record.denom_500_available, "Rs. 500"),
                (record.balance_100_qty, record.denom_100_available, "Rs. 100"),
                (record.balance_50_qty, record.denom_50_available, "Rs. 50"),
                (record.balance_20_qty, record.denom_20_available, "Rs. 20"),
                (record.balance_10_qty, record.denom_10_available, "Rs. 10"),
                (record.balance_5_qty, record.denom_5_available, "Rs. 5"),
                (record.balance_2_qty, record.denom_2_available, "Rs. 2"),
                (record.balance_1_qty, record.denom_1_available, "Rs. 1"),
            ]

            for needed, available, denomination in checks:
                if needed > available:
                    errors.append(
                        f"{denomination}: Need {needed}, Available {available}"
                    )

            if errors:
                error_msg = _(
                    "Not enough balance denominations available:\n"
                ) + "\n".join(errors)
                raise UserError(error_msg)

    def action_auto_calculate(self):
        """Auto-calculate denomination breakdown"""
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
                "message": _("Denomination breakdown calculated successfully."),
                "type": "success",
            },
        }

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

        # Get float request
        float_request = None
        if self.request_id:
            float_request = self.request_id.float_request_id
        elif self.iou_request_id:
            float_request = self.iou_request_id.float_request_id
        elif self.reimbursement_id:
            float_request = self.reimbursement_id.float_request_id

        if not float_request:
            raise UserError(_("No float request found."))

        # Get current denomination and update it
        current_denom = self.env["float.denomination"].search(
            [("float_request_id", "=", float_request.id)],
            order="last_updated desc",
            limit=1,
        )

        if current_denom:
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

            if self.reimbursement_id:
                current_denom.add_denomination_from_reimbursement(denomination_used)
            else:
                current_denom.update_denomination_after_reimbursement(denomination_used)

        # Create message and update request state
        denomination_details = self._create_denomination_message()

        if self.request_id:
            self.request_id.state = "cash_issued"
            self.request_id.message_post(body=denomination_details)
        elif self.iou_request_id:
            self.iou_request_id.state = "pending_bill_submission"
            self.iou_request_id.cashReceivedByEmployee = True
            self.iou_request_id.message_post(body=denomination_details)
        elif self.reimbursement_id:
            self.reimbursement_id.received_amount = self.selected_amount
            self.reimbursement_id.cash_received_by_handler = True
            self.reimbursement_id.message_post(body=denomination_details)

        return {
            "type": "ir.actions.act_window_close",
        }

    def _create_denomination_message(self):
        """Create denomination breakdown message"""
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
                <tr><th>Total:</th><th></th><th>Rs. {self.selected_amount:,.2f}</th></tr>
            </tfoot>
        </table>
        """

        return message

    def action_cancel(self):
        """Cancel the wizard"""
        return {
            "type": "ir.actions.act_window_close",
        }
