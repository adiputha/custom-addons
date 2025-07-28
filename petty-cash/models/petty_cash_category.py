from odoo import models, fields, api, _

class PettyCashCategory(models.Model):
    _name = 'petty.cash.category'
    _description = 'Petty Cash Category'
    _order = 'name'
    _rec_name = 'name'  # Use 'name' as the display name in views

    name = fields.Char(
        string='Category Name',
        required=True,
        help='Name of the petty cash category',
    )

    code = fields.Char(
        string='Category Code',
        required=True,
        help='Unique code for the petty cash category',
    )

    description = fields.Text(
        string='Description',
        help='Detailed description of the petty cash category',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to make this category inactive',
    )

    color = fields.Integer(
        string='Color',
        help='Color code for the category',
    )

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', _('The category code must be unique.')),
        ('unique_name', 'UNIQUE(name)', _('The category name must be unique.')),
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []

        if name:
            categories = self.search([
                '|',
                ('name', operator, name),
                ('code', operator, name)
            ] + args, limit=limit)
            return categories.name_get()

        return super().name_search(name, args, operator, limit)
    
    def name_get(self):
        result = []
        for category in self:
            if category.code:
                name= f"[{category.code}] {category.name}"
            else:
                name = category.name
            result.append((category.id, name))
        return result
    
    def action_save_and_close(self):
        """Save record and return to list view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'petty.cash.category',
            'view_mode': 'list',
            'target': 'current',
        }

    def action_save_and_new(self):
        """Save record and open new form"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'petty.cash.category',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_active': True},
        }
