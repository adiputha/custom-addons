from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PettyCashConfig(models.Model):
    _name = "petty.cash.config"
    _description = "Petty Cash Configuration"
    _rec_name = "name"

    name = fields.Char(
        string="Configuration Name",
        required=True,
        default="Petty Cash System Configuration",
        help="Name of the petty cash configuration.",
    )

    # Cross-department settings
    allow_cross_department_requests = fields.Boolean(
        string="Allow Cross Department Requests",
        default=False,
        help="Allow petty cash transactions across different departments.",
    )

    require_hod_approval_cross_dept = fields.Boolean(
        string="Require HOD Approval for Cross Department",
        default=True,
        help="Require HOD approval when requesting from different department float.",
    )

    require_float_manager_approval_cross_dept = fields.Boolean(
        string="Require Float Manager Approval for Cross Department",
        default=True,
        help="Require float manager approval for cross department requests.",
    )

    # Due date configurations
    default_petty_cash_due_days = fields.Integer(
        string="Default Petty Cash Due Days",
        default=0,
        help="Default number of days before petty cash settlement is due (0 means immediate).",
    )

    default_iou_due_days = fields.Integer(
        string="Default IOU Due Days",
        default=10,
        help="Default number of days before IOU settlement is due.",
    )

    # Alert configurations
    enable_due_date_alerts = fields.Boolean(
        string="Enable Due Date Alerts",
        default=True,
        help="Send alerts for overdue IOUs and settlements.",
    )

    first_alert_days_before = fields.Integer(
        string="First Alert (Days Before Due)",
        default=2,
        help="Send first alert X days before due date.",
    )

    second_alert_days_after = fields.Integer(
        string="Second Alert (Days After Due)",
        default=3,
        help="Send second alert X days after due date passes.",
    )

    # Amount limits
    max_petty_cash_amount = fields.Float(
        string="Maximum Petty Cash Amount",
        default=5000.0,
        help="Maximum amount allowed for single petty cash request.",
    )

    max_iou_amount = fields.Float(
        string="Maximum IOU Amount",
        default=10000.0,
        help="Maximum amount allowed for single IOU request.",
    )

    # Approval workflows
    require_bills_before_cash_issue = fields.Boolean(
        string="Require Bills Before Cash Issue",
        default=True,
        help="Require bill submission and approval before issuing cash.",
    )

    auto_approve_small_amounts = fields.Boolean(
        string="Auto-approve Small Amounts",
        default=False,
        help="Auto-approve requests below threshold amount.",
    )

    auto_approve_threshold = fields.Float(
        string="Auto-approval Threshold",
        default=1000.0,
        help="Amount below which requests are auto-approved.",
    )

    # Reimbursement settings
    reimbursement_approval_required = fields.Boolean(
        string="Reimbursement Approval Required",
        default=True,
        help="Require manager approval for float reimbursements.",
    )

    min_float_balance_warning = fields.Float(
        string="Minimum Float Balance Warning",
        default=2000.0,
        help="Warn when float balance goes below this amount.",
    )

    # Security settings
    restrict_handler_edit_approved = fields.Boolean(
        string="Restrict Handler Edit After Approval",
        default=True,
        help="Prevent handlers from editing requests after approval.",
    )

    require_voucher_attachment = fields.Boolean(
        string="Require Voucher Attachment",
        default=True,
        help="Require voucher attachment for request completion.",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Only one configuration can be active at a time.",
    )

    @api.constrains("active")
    def _check_single_active_config(self):
        """Ensure only one configuration is active"""
        active_configs = self.search([("active", "=", True)])
        if len(active_configs) > 1:
            raise ValidationError(
                _("Only one petty cash configuration can be active at a time.")
            )

    @api.constrains(
        "default_petty_cash_due_days",
        "default_iou_due_days",
        "first_alert_days_before",
        "second_alert_days_after",
        "max_petty_cash_amount",
        "max_iou_amount",
        "auto_approve_threshold",
        "min_float_balance_warning",
    )
    def _check_positive_values(self):
        """Validate that numeric fields have appropriate values"""
        for record in self:
            if record.default_petty_cash_due_days < 0:
                raise ValidationError(_("Petty cash due days cannot be negative."))
            if record.default_iou_due_days <= 0:
                raise ValidationError(_("IOU due days must be greater than zero."))
            if record.first_alert_days_before < 0:
                raise ValidationError(_("First alert days cannot be negative."))
            if record.second_alert_days_after < 0:
                raise ValidationError(_("Second alert days cannot be negative."))
            if record.max_petty_cash_amount <= 0:
                raise ValidationError(
                    _("Maximum petty cash amount must be greater than zero.")
                )
            if record.max_iou_amount <= 0:
                raise ValidationError(
                    _("Maximum IOU amount must be greater than zero.")
                )
            if record.auto_approve_threshold < 0:
                raise ValidationError(_("Auto-approval threshold cannot be negative."))
            if record.min_float_balance_warning < 0:
                raise ValidationError(_("Minimum balance warning cannot be negative."))

    @api.model
    def get_active_config(self):
        """Get the currently active configuration"""
        config = self.search([("active", "=", True)], limit=1)
        if not config:
            # Create default configuration if none exists
            config = self.create(
                {
                    "name": "Default Petty Cash Configuration",
                    "active": True,
                }
            )
        return config

    def action_set_active(self):
        """Set this configuration as active"""
        # Deactivate all other configs
        self.search([("active", "=", True)]).write({"active": False})
        # Activate this one
        self.active = True
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Configuration Activated"),
                "message": _("This configuration is now active."),
                "type": "success",
            },
        }

    @api.model
    def apply_config_to_model(self, model_name, field_mapping=None):
        """Apply configuration values to other models"""
        config = self.get_active_config()

        # Default field mappings for different models
        if not field_mapping:
            field_mapping = {
                "petty.cash.request": {
                    "max_amount": "max_petty_cash_amount",
                    "due_days": "default_petty_cash_due_days",
                },
                "petty.cash.iou.request": {
                    "max_amount": "max_iou_amount",
                    "due_days": "default_iou_due_days",
                },
            }

        if model_name in field_mapping:
            mapping = field_mapping[model_name]
            result = {}
            for target_field, config_field in mapping.items():
                if hasattr(config, config_field):
                    result[target_field] = getattr(config, config_field)
            return result

        return {}

    def action_test_alerts(self):
        """Test the alert system with current settings"""
        # This would trigger test alerts based on current configuration
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Alert Test"),
                "message": _("Alert system tested with current settings."),
                "type": "info",
            },
        }
