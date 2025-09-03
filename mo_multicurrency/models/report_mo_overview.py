from odoo import models, fields, api
import copy


class ReportMoOverviewDual(models.AbstractModel):
    _name = "report.mo_multicurrency.action_report_mo_overview_dual"
    _inherit = "report.mrp.report_mo_overview"
    _description = "Manufacturing Order Overview Dual Currency Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Override to add USD conversion"""
        result = super()._get_report_values(docids, data)
        
        # Convert all docs to include USD values
        if 'docs' in result:
            for doc in result['docs']:
                self._add_usd_values(doc)
        
        return result

    def _add_usd_values(self, doc_data):
        """Add USD converted values to all cost fields - Updated to include cost breakdown"""
        usd_currency = self.env.ref('base.USD')
        lkr_currency = self.env.company.currency_id
        
        # Convert summary
        if 'summary' in doc_data:
            self._convert_record_to_dual_currency(doc_data['summary'], lkr_currency, usd_currency)
        
        # Convert components
        for component in doc_data.get('components', []):
            if 'summary' in component:
                self._convert_record_to_dual_currency(component['summary'], lkr_currency, usd_currency)
            
            # Convert replenishments
            for replenishment in component.get('replenishments', []):
                if 'summary' in replenishment:
                    self._convert_record_to_dual_currency(replenishment['summary'], lkr_currency, usd_currency)
        
        # Convert operations
        operations = doc_data.get('operations', {})
        if 'summary' in operations:
            self._convert_record_to_dual_currency(operations['summary'], lkr_currency, usd_currency)
        
        for operation in operations.get('details', []):
            self._convert_record_to_dual_currency(operation, lkr_currency, usd_currency)
        
        # Convert byproducts
        byproducts = doc_data.get('byproducts', {})
        if 'summary' in byproducts:
            self._convert_record_to_dual_currency(byproducts['summary'], lkr_currency, usd_currency)
        
        for byproduct in byproducts.get('details', []):
            self._convert_record_to_dual_currency(byproduct, lkr_currency, usd_currency)
        
        # Convert extras
        if 'extras' in doc_data:
            self._convert_extras_to_dual_currency(doc_data['extras'], lkr_currency, usd_currency)
            
        # Convert cost breakdown
        if 'cost_breakdown' in doc_data:
            self._convert_cost_breakdown_to_dual_currency(doc_data['cost_breakdown'], lkr_currency, usd_currency)

    def _convert_record_to_dual_currency(self, record, lkr_currency, usd_currency):
        """Convert cost fields in a record to dual currency"""
        cost_fields = ['mo_cost', 'bom_cost', 'real_cost', 'unit_cost']
        company = self.env.company
        
        for field in cost_fields:
            if field in record and record[field]:
                lkr_value = record[field]
                usd_value = lkr_currency._convert(
                    lkr_value, usd_currency, company, fields.Date.today()
                )
                
                # Store both values
                record[f'{field}_lkr'] = lkr_value
                record[f'{field}_usd'] = usd_value
        
        # Add currency references
        record['currency_lkr'] = lkr_currency
        record['currency_usd'] = usd_currency

    def _convert_extras_to_dual_currency(self, extras, lkr_currency, usd_currency):
        """Convert extras dictionary to dual currency"""
        company = self.env.company
        
        for key, value in list(extras.items()):
            if isinstance(value, (int, float)) and 'cost' in key.lower():
                usd_value = lkr_currency._convert(
                    value, usd_currency, company, fields.Date.today()
                )
                extras[f'{key}_lkr'] = value
                extras[f'{key}_usd'] = usd_value

    def _convert_cost_breakdown_to_dual_currency(self, cost_breakdown, lkr_currency, usd_currency):
        """Convert cost breakdown items to dual currency"""
        company = self.env.company
        
        for line in cost_breakdown:
            cost_fields = ['unit_avg_cost_component', 'unit_avg_cost_operation', 'unit_avg_total_cost']
            
            for field in cost_fields:
                if field in line and line[field]:
                    lkr_value = line[field]
                    usd_value = lkr_currency._convert(
                        lkr_value, usd_currency, company, fields.Date.today()
                    )
                    
                    line[f'{field}_lkr'] = lkr_value
                    line[f'{field}_usd'] = usd_value