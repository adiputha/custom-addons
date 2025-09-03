from odoo import models, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    def action_report_mo_overview_dual_currency(self):
        """Open dual currency report for Manufacturing Orders"""
        return {
            'type': 'ir.actions.report',
            'report_name': 'mo_multicurrency.action_report_mo_overview_dual',
            'report_type': 'qweb-html',
            'data': {
                'show_usd': True,
                'show_lkr': True,
            },
            'context': {'active_ids': self.ids}
        }