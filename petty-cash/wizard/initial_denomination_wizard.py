import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class InitialDenominationWizard(models.TransientModel):
    _name = "initial.denomination.wizard"
    _description = "Initial Denomination Wizard"

    float_request_id = fields.Many2one(
        "float.request",
        string="Float Request",
        required=True,
        readonly=True,
        help="The float request for which initial denominations are being set.",
    )

    float_name = fields.Char(
        related="float_request_id.name",
        string="Float Name",
        readonly=True,
        help="The name of the float request.",
    )

    initial_amount = fields.Float(
        string="Initial Amount",
        related="float_request_id.initial_amount",
        readonly=True,
    )

    department_name = fields.Char(
        related="float_request_id.department_id.name",
        string="Department",
        readonly=True,
    )

    setup_method = fields.Selection(
        [
            ("auto", "Auto Calculate (Recommended)"),
            ("manual", "Manual Entry"),
            ("template", "Use Template"),
        ],
        string="setup Method",
        default="auto",
        required=True,
        help="Choose how to set up the initial denominations.",
    )

    template_type = fields.Selection(
        [
            ("balanced", "Balanced Mix"),
            ("large_notes", "Prefer Large Notes"),
            ("small_change", "More Small Change"),
            ("custom", "Custom Template"),
        ],
        string="Template Type",
        default="balanced",
        help="Select a template for denomination setup.",
    )

    # Denomination fields
    denom_5000_qty = fields.Integer(string="Rs. 5,000 Notes", default=0)
    denom_1000_qty = fields.Integer(string="Rs. 1,000 Notes", default=0)
    denom_500_qty = fields.Integer(string="Rs. 500 Notes", default=0)
    denom_100_qty = fields.Integer(string="Rs. 100 Notes", default=0)
    denom_50_qty = fields.Integer(string="Rs. 50 Notes", default=0)
    denom_20_qty = fields.Integer(string="Rs. 20 Notes", default=0)
    denom_10_qty = fields.Integer(string="Rs. 10 Coins", default=0)
    denom_5_qty = fields.Integer(string="Rs. 5 Coins", default=0)
    denom_2_qty = fields.Integer(string="Rs. 2 Coins", default=0)
    denom_1_qty = fields.Integer(string="Rs. 1 Coins", default=0)

    calculated_total = fields.Float(
        string="Calculated Total",
        compute="_compute_calculated_total",
        store=True,
        help="Total amount calculated from the denominations.",
    )

    difference = fields.Float(
        string="Difference",
        compute="_compute_difference",
        store=True,
    )

    is_balanced = fields.Boolean(
        string="Is Balanced",
        compute="_compute_is_balanced",
        help="Indicates if the total denominations match the float request's initial amount.",
    )

    denom_5000_amount = fields.Float(
        string="Rs. 5,000 Amount",
        compute="_compute_denomination_amounts",
    )
    denom_1000_amount = fields.Float(
        string="Rs. 1,000 Amount",
        compute="_compute_denomination_amounts",
    )
    denom_500_amount = fields.Float(
        string="Rs. 500 Amount",
        compute="_compute_denomination_amounts",
    )
    denom_100_amount = fields.Float(
        string="Rs. 100 Amount",
        compute="_compute_denomination_amounts",
    )
    
    denom_50_amount = fields.Float(
        string="Rs. 50 Amount",
        compute="_compute_denomination_amounts",
    )
    
    denom_20_amount = fields.Float(
        string="Rs. 20 Amount",
        compute="_compute_denomination_amounts",
    )
    
    denom_10_amount = fields.Float(
        string="Rs. 10 Amount",
        compute="_compute_denomination_amounts",
    )
    
    denom_5_amount = fields.Float(
        string="Rs. 5 Amount",
        compute="_compute_denomination_amounts",
    )
    
    denom_2_amount = fields.Float(
        string="Rs. 2 Amount",
        compute="_compute_denomination_amounts",
    )
    
    denom_1_amount = fields.Float(
        string="Rs. 1 Amount",
        compute="_compute_denomination_amounts",
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        if (
            self.env.context.get("active_id")
            and self.env.context.get("active_model") == "float.request"
        ):
            defaults["float_request_id"] = self.env.context["active_id"]
        elif self.env.context.get("default_float_request_id"):
            defaults["float_request_id"] = self.env.context["default_float_request_id"]

        return defaults

    def _suggest_denomination_breakdown(self, amount):
        """Suggest a breakdown of denominations for the given amount."""
        remaining = amount
        breakdown = {}

        denominations = [
            (5000, "denom_5000_qty", 10),  # (value, field_name, max_notes)
            (1000, "denom_1000_qty", 20),
            (500, "denom_500_qty", 15),
            (100, "denom_100_qty", 30),
            (50, "denom_50_qty", 10),
            (20, "denom_20_qty", 25),
            (10, "denom_10_qty", 50),
            (5, "denom_5_qty", 50),
            (2, "denom_2_qty", 50),
            (1, "denom_1_qty", 100),
        ]

        for value, field_name, max_notes in denominations:
            if remaining <= 0:
                breakdown[field_name] = 0
                continue

            # Calculate optimal quantity for this denomination
            needed = min(int(remaining / value), max_notes)
            breakdown[field_name] = needed
            remaining -= needed * value

        return breakdown

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
    def _compute_calculated_total(self):
        for record in self:
            record.calculated_total = (
                (record.denom_5000_qty * 5000)
                + (record.denom_1000_qty * 1000)
                + (record.denom_500_qty * 500)
                + (record.denom_100_qty * 100)
                + (record.denom_50_qty * 50)
                + (record.denom_20_qty * 20)
                + (record.denom_10_qty * 10)
                + (record.denom_5_qty * 5)
                + (record.denom_2_qty * 2)
                + (record.denom_1_qty * 1)
            )

    @api.depends("calculated_total", "initial_amount")
    def _compute_difference(self):
        for record in self:
            record.difference = record.calculated_total - record.initial_amount

    @api.depends("difference")
    def _compute_is_balanced(self):
        for record in self:
            record.is_balanced = abs(record.difference) < 0.01

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
    def _check_negative_values(self):
        for record in self:
            denomination_fields = [
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
            ]

            for field in denomination_fields:
                if getattr(record, field) < 0:
                    raise ValidationError(
                        _("Denomination quantities cannot be negative.")
                    )

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
    def _compute_denomination_amounts(self):
        for record in self:
            record.denom_5000_amount = record.denom_5000_qty * 5000
            record.denom_1000_amount = record.denom_1000_qty * 1000
            record.denom_500_amount = record.denom_500_qty * 500
            record.denom_100_amount = record.denom_100_qty * 100
            record.denom_50_amount = record.denom_50_qty * 50
            record.denom_20_amount = record.denom_20_qty * 20
            record.denom_10_amount = record.denom_10_qty * 10  
            record.denom_5_amount = record.denom_5_qty * 5
            record.denom_2_amount = record.denom_2_qty * 2
            record.denom_1_amount = record.denom_1_qty * 1

    @api.onchange("setup_method")
    def _onchange_setup_method(self):
        """Auto-apply setup method changes"""
        if self.setup_method == "auto":
            self.action_auto_calculate()
        elif self.setup_method == "template":
            self._apply_template()

    @api.onchange("template_type")
    def _onchange_template_type(self):
        """Auto-apply template type changes"""
        if self.template_type == "template":
            self._apply_template()

    def _apply_template(self):
        """Apply the selected template for denomination setup."""
        amount = self.initial_amount

        if self.template_type == "balanced":
            breakdown = self._get_balanced_template(amount)
        elif self.template_type == "large_notes":
            breakdown = self._get_large_notes_template(amount)
        elif self.template_type == "small_change":
            breakdown = self._get_small_change_template(amount)
        else:
            return

        for field, qty in breakdown.items():
            setattr(self, field, qty)

    def _get_balanced_template(self, amount):
        """Balanced template for denomination setup."""
        remaining = amount
        breakdown = {}

        large_amount = amount * 0.6  # 60% in large denominations
        breakdown["denom_5000_qty"] = min(int(large_amount * 0.4 / 5000), 8)
        remaining -= breakdown["denom_5000_qty"] * 5000

        breakdown["denom_1000_qty"] = min(int(large_amount * 0.3 / 1000), 15)
        remaining -= breakdown["denom_1000_qty"] * 1000

        breakdown["denom_500_qty"] = min(int(large_amount * 0.2 / 500), 10)
        remaining -= breakdown["denom_500_qty"] * 500

        breakdown["denom_100_qty"] = min(int(large_amount * 0.6 / 100), 20)
        remaining -= breakdown["denom_100_qty"] * 100

        self._fill_remaining_optimally(breakdown, remaining)

        return breakdown

    def _get_large_notes_template(self, amount):
        """Prefer larger denominations"""
        remaining = amount
        breakdown = {}

        breakdown["denom_5000_qty"] = min(int(remaining / 5000), 10)
        remaining -= breakdown["denom_5000_qty"] * 5000

        breakdown["denom_1000_qty"] = min(int(remaining / 1000), 20)
        remaining -= breakdown["denom_1000_qty"] * 1000

        breakdown["denom_500_qty"] = min(int(remaining / 500), 8)
        remaining -= breakdown["denom_500_qty"] * 500

        self._fill_remaining_optimally(breakdown, remaining)

        return breakdown

    def _get_small_change_template(self, amount):
        """More small change"""
        remaining = amount
        breakdown = {}

        breakdown["denom_5000_qty"] = min(int(remaining * 0.3 / 5000), 5)
        remaining -= breakdown["denom_5000_qty"] * 5000

        breakdown["denom_1000_qty"] = min(int(remaining * 0.4 / 1000), 8)
        remaining -= breakdown["denom_1000_qty"] * 1000

        breakdown["denom_500_qty"] = min(int(remaining * 0.3 / 500), 15)
        remaining -= breakdown["denom_500_qty"] * 500

        breakdown["denom_100_qty"] = min(int(remaining * 0.4 / 100), 30)
        remaining -= breakdown["denom_100_qty"] * 100

        breakdown["denom_50_qty"] = min(int(remaining * 0.3 / 50), 20)
        remaining -= breakdown["denom_50_qty"] * 50

        breakdown["denom_20_qty"] = min(int(remaining * 0.4 / 20), 25)
        remaining -= breakdown["denom_20_qty"] * 20

        self._fill_remaining_optimally(breakdown, remaining)
        return breakdown

    def _fill_remaining_optimally(self, breakdown, remaining):
        """Fill remaining amount with smaller denominations optimally."""
        small_denoms = [
            ("denom_100_qty", 100, 50),
            ("denom_50_qty", 50, 20),
            ("denom_20_qty", 20, 50),
            ("denom_10_qty", 10, 100),
            ("denom_5_qty", 5, 50),
            ("denom_2_qty", 2, 50),
            ("denom_1_qty", 1, 100),
        ]

        for field, value, max_qty in small_denoms:
            if remaining <= 0:
                breakdown.setdefault(field, 0)
                continue

            current_qty = breakdown.get(field, 0)
            additional = min(int(remaining / value), max_qty - current_qty)
            if additional > 0:
                breakdown[field] = current_qty + additional
                remaining -= additional * value
            else:
                breakdown.setdefault(field, 0)

    def action_auto_calculate(self):
        """Auto-calculate optimal denomination breakdown"""
        self.ensure_one()
        amount = self.initial_amount

        if amount <= 0:
            raise UserError(_("Initial amount must be greater than zero."))

        breakdown = self._get_balanced_template(amount)

        for field, qty in breakdown.items():
            setattr(self, field, qty)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Auto-calculated"),
                "message": _(
                    "Optimal denomination breakdown calculated successfully.."
                ),
                "type": "success",
            },
        }

    def action_clear_all(self):
        """Clear all denomination fields"""
        self.ensure_one()
        clear_values  = {
            "denom_5000_qty": 0,
            "denom_1000_qty": 0,
            "denom_500_qty": 0,
            "denom_100_qty": 0,
            "denom_50_qty": 0,
            "denom_20_qty": 0,
            "denom_10_qty": 0,
            "denom_5_qty": 0,
            "denom_2_qty": 0,
            "denom_1_qty": 0,
        }
        
        try:

            for field, value in clear_values.items():
                setattr(self, field, value)
                
        except Exception as e:
            return {
            'type': 'ir.actions.act_window',
            'name': 'Setup Initial Denominations',
            'res_model': 'initial.denomination.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_float_request_id': self.float_request_id.id,
            },
        }

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Cleared"),
                "message": _("All denomination quantities cleared."),
                "type": "info",
            },
        }

    def action_create_denomination(self):
        """Create the initial denomination record"""
        self.ensure_one()

        # Validate that total matches
        if not self.is_balanced:
            raise UserError(
                _(
                    "Total amount (Rs. %.2f) does not match float amount (Rs. %.2f). "
                    "Difference: Rs. %.2f\n\n"
                    "Please adjust the denominations to match the float request amount."
                )
                % (self.calculated_total, self.initial_amount, self.difference)
            )

        # Check if denomination record already exists
        existing_denomination = self.env["float.denomination"].search(
            [("float_request_id", "=", self.float_request_id.id)]
        )

        if existing_denomination:
            raise UserError(_("Initial denomination record already exists for this float."))

        # Create the denomination record
        denomination_data = {
            "float_request_id": self.float_request_id.id,
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

        try:
            # Create the denomination record
            self.env["float.denomination"].create(denomination_data)

            # Log message on float request
            message = self._create_denomination_message()
            self.float_request_id.message_post(body=message)

            # Update float request current denomination
            self.float_request_id._compute_current_denomination()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("Initial denomination record created successfully."),
                    "type": "success",
                    "sticky": False,
                },
            }

        except Exception as e:
            _logger.error("Error creating initial denomination: %s", e)
            raise UserError(
                _("Failed to create initial denomination record. Please try again.")
            )
            
    def _create_success_message(self):
        """Create a success message for the user"""
        message = f"""
        <div class="alert alert-success">
            <h4>Initial Denomination Created Successfully!</h4>
            <p><strong>Setup Method:</strong> {dict(self._fields['setup_method'].selection)[self.setup_method]}</p>

        </div>
        <table class="table table-sm table-striped">
            <thead class="table-primary">
                <tr>
                    <th>Denomination</th>
                    <th>Quantity</th>
                    <th>Amount</th>
                </tr>
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
                amount = qty * value
                message += f"""
                <tr>
                    <td>{label}</td>
                    <td>{qty}</td>
                    <td>Rs. {amount:,.2f}</td>
                </tr>
                """
        message += f"""
            </tbody>
            <tfoot class="table-success">
                <tr>
                    <th>Total</th>
                    <th></th>
                    <th>Rs. {self.calculated_total:,.2f}</th>
                </tr>
            </tfoot>
        </table>
        """
        return message

    def _create_denomination_message(self):
        """Create a message showing the denomination breakdown"""
        message = f"""
        <h4>Initial Denomination Setup:</h4>
        <table class="table table-sm">
            <tr><td>Rs. 5,000 Notes:</td><td>{self.denom_5000_qty}</td><td>= Rs. {self.denom_5000_qty * 5000:,.2f}</td></tr>
            <tr><td>Rs. 1,000 Notes:</td><td>{self.denom_1000_qty}</td><td>= Rs. {self.denom_1000_qty * 1000:,.2f}</td></tr>
            <tr><td>Rs. 500 Notes:</td><td>{self.denom_500_qty}</td><td>= Rs. {self.denom_500_qty * 500:,.2f}</td></tr>
            <tr><td>Rs. 100 Notes:</td><td>{self.denom_100_qty}</td><td>= Rs. {self.denom_100_qty * 100:,.2f}</td></tr>
            <tr><td>Rs. 50 Notes:</td><td>{self.denom_50_qty}</td><td>= Rs. {self.denom_50_qty * 50:,.2f}</td></tr>
            <tr><td>Rs. 20 Notes:</td><td>{self.denom_20_qty}</td><td>= Rs. {self.denom_20_qty * 20:,.2f}</td></tr>
            <tr><td>Rs. 10 Coins:</td><td>{self.denom_10_qty}</td><td>= Rs. {self.denom_10_qty * 10:,.2f}</td></tr>
            <tr><td>Rs. 5 Coins:</td><td>{self.denom_5_qty}</td><td>= Rs. {self.denom_5_qty * 5:,.2f}</td></tr>
            <tr><td>Rs. 2 Coins:</td><td>{self.denom_2_qty}</td><td>= Rs. {self.denom_2_qty * 2:,.2f}</td></tr>
            <tr><td>Rs. 1 Coins:</td><td>{self.denom_1_qty}</td><td>= Rs. {self.denom_1_qty * 1:,.2f}</td></tr>
            <tr><td><strong>Total:</strong></td><td></td><td><strong>Rs. {self.calculated_total:,.2f}</strong></td></tr>
        </table>
        """
        return message

    def action_cancel(self):
        """Cancel the wizard"""
        return {"type": "ir.actions.act_window_close"}
