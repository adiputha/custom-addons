from odoo import models, fields, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    float_manager_department_ids = fields.Many2many(
        'hr.department',
        'department_float_manager_rel',
        'user_id',
        'department_id',
        string='Float Manager Departments',
        help='Departments for which this user can manage floats'
    )

    # Track managed floats
    managed_float_ids = fields.One2many(
        'float.request',
        'float_manager_id',
        string='Managed Floats',
        help='Floats managed by this user'
    )

    managed_float_count = fields.Integer(
        string='Managed Floats Count',
        compute='_compute_managed_float_count'
    )

    @api.depends('managed_float_ids.state')
    def _compute_managed_float_count(self):
        """Compute number of active floats managed by this user"""
        for user in self:
            user.managed_float_count = len(user.managed_float_ids.filtered(
                lambda f: f.state == 'approved'
            ))

    def action_view_managed_floats(self):
        """Open floats managed by this user"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Managed Floats',
            'res_model': 'float.request',
            'view_mode': 'kanban,list,form',
            'domain': [('float_manager_id', '=', self.id)],
            'context': {
                'search_default_approved': 1,
            }
        }