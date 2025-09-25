from odoo import models, fields, api, _

class HrDepartment(models.Model):
    _inherit = "hr.department"

    float_manager_ids = fields.Many2many(
        'res.users',
        'department_float_manager_rel',
        'department_id',
        'user_id',
        string="Float Managers",
        help='Users who can manage floats for this department',
        domain=[('groups_id', 'in', lambda self: [self.env.ref('petty-cash.group_petty_cash_float_manager').id])]
    )

    active_float_count = fields.Integer(
        string='Active Floats',
        compute='_compute_active_float_count'
    )

    @api.depends('float_request_ids.state')
    def _compute_active_float_count(self):
        """Compute number of active floats for this department"""
        for department in self:
            department.active_float_count = self.env['float.request'].search_count([
                ('department_id', '=', department.id),
                ('state', '=', 'approved')
            ])

    # Reverse relation to float requests
    float_request_ids = fields.One2many(
        'float.request',
        'department_id',
        string='Float Requests',
        help='Float requests for this department'
    )

    def action_view_department_floats(self):
        """Open float requests for this department"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Floats - {self.name}',
            'res_model': 'float.request',
            'view_mode': 'list,form',
            'domain': [('department_id', '=', self.id)],
            'context': {
                'default_department_id': self.id,
                'search_default_approved': 1,
            }
        }

