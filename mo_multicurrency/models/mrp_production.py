from odoo import models, fields, api
import base64

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    def action_report_mo_overview_dual_currency(self):
        """Generate comprehensive dual currency HTML report"""
        
        try:
            # Generate complete report data
            report_data = self._generate_dual_currency_data()
            
            # Create HTML report
            html_content = self._generate_html_report(report_data)
            
            # Return as downloadable HTML file
            return {
                'type': 'ir.actions.act_url',
                'url': 'data:text/html;charset=utf-8;base64,' + base64.b64encode(html_content.encode('utf-8')).decode(),
                'target': 'new',
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Failed to generate report: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def _generate_dual_currency_data(self):
        """Generate comprehensive dual currency data"""
        data = {
            'mo_name': self.name,
            'product_name': self.product_id.name,
            'quantity': self.product_qty,
            'state': self.state,
            'date_planned_start': self.date_planned_finished or self.create_date,
            'components': [],
            'operations': [],
            'totals': {}
        }
        
        # Calculate component costs
        total_component_cost_lkr = 0
        total_component_cost_usd = 0
        
        if self.bom_id:
            for line in self.bom_id.bom_line_ids:
                component_cost_lkr = line.product_id.standard_price * line.product_qty * self.product_qty
                component_cost_usd = round(component_cost_lkr / 300, 2)  # Simple conversion
                
                total_component_cost_lkr += component_cost_lkr
                total_component_cost_usd += component_cost_usd
                
                data['components'].append({
                    'name': line.product_id.name,
                    'quantity': line.product_qty * self.product_qty,
                    'unit_cost_lkr': line.product_id.standard_price,
                    'unit_cost_usd': round(line.product_id.standard_price / 300, 2),
                    'total_cost_lkr': component_cost_lkr,
                    'total_cost_usd': component_cost_usd,
                    'uom': line.product_id.uom_id.name
                })
        
        # Calculate operation costs (if any)
        total_operation_cost_lkr = 0
        total_operation_cost_usd = 0
        
        for workorder in self.workorder_ids:
            if workorder.operation_id:
                # Simple operation cost calculation
                operation_cost_lkr = workorder.duration_expected * 50  # 50 LKR per hour
                operation_cost_usd = round(operation_cost_lkr / 300, 2)
                
                total_operation_cost_lkr += operation_cost_lkr
                total_operation_cost_usd += operation_cost_usd
                
                data['operations'].append({
                    'name': workorder.operation_id.name,
                    'duration': workorder.duration_expected,
                    'cost_lkr': operation_cost_lkr,
                    'cost_usd': operation_cost_usd
                })
        
        # Calculate totals
        data['totals'] = {
            'components_lkr': total_component_cost_lkr,
            'components_usd': total_component_cost_usd,
            'operations_lkr': total_operation_cost_lkr,
            'operations_usd': total_operation_cost_usd,
            'total_lkr': total_component_cost_lkr + total_operation_cost_lkr,
            'total_usd': total_component_cost_usd + total_operation_cost_usd,
            'unit_cost_lkr': (total_component_cost_lkr + total_operation_cost_lkr) / self.product_qty if self.product_qty else 0,
            'unit_cost_usd': (total_component_cost_usd + total_operation_cost_usd) / self.product_qty if self.product_qty else 0
        }
        
        return data
    
    def _generate_html_report(self, data):
        """Generate HTML report content"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Manufacturing Order Overview - Dual Currency</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
                th {{ background-color: #e9ecef; }}
                .currency-header {{ background-color: #d4edda; }}
                .total-row {{ background-color: #f8f9fa; font-weight: bold; }}
                .text-right {{ text-align: right; }}
                h2 {{ color: #495057; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Manufacturing Order Overview (LKR & USD)</h1>
                <p><strong>MO:</strong> {data['mo_name']}</p>
                <p><strong>Product:</strong> {data['product_name']}</p>
                <p><strong>Quantity:</strong> {data['quantity']}</p>
                <p><strong>Status:</strong> {data['state'].title()}</p>
                <p><strong>Date:</strong> {data['date_planned_start']}</p>
            </div>
        """
        
        # Components table
        if data['components']:
            html += """
            <h2>Components</h2>
            <table>
                <thead>
                    <tr>
                        <th>Component</th>
                        <th>Quantity</th>
                        <th>UoM</th>
                        <th class="currency-header">Unit Cost (LKR)</th>
                        <th class="currency-header">Unit Cost (USD)</th>
                        <th class="currency-header">Total Cost (LKR)</th>
                        <th class="currency-header">Total Cost (USD)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for component in data['components']:
                html += f"""
                    <tr>
                        <td>{component['name']}</td>
                        <td class="text-right">{component['quantity']}</td>
                        <td>{component['uom']}</td>
                        <td class="text-right">{component['unit_cost_lkr']:.2f}</td>
                        <td class="text-right">{component['unit_cost_usd']:.2f}</td>
                        <td class="text-right">{component['total_cost_lkr']:.2f}</td>
                        <td class="text-right">{component['total_cost_usd']:.2f}</td>
                    </tr>
                """
            
            html += f"""
                    <tr class="total-row">
                        <td colspan="5">Total Components Cost</td>
                        <td class="text-right">{data['totals']['components_lkr']:.2f}</td>
                        <td class="text-right">{data['totals']['components_usd']:.2f}</td>
                    </tr>
                </tbody>
            </table>
            """
        
        # Operations table
        if data['operations']:
            html += """
            <h2>Operations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Operation</th>
                        <th>Duration (hours)</th>
                        <th class="currency-header">Cost (LKR)</th>
                        <th class="currency-header">Cost (USD)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for operation in data['operations']:
                html += f"""
                    <tr>
                        <td>{operation['name']}</td>
                        <td class="text-right">{operation['duration']:.2f}</td>
                        <td class="text-right">{operation['cost_lkr']:.2f}</td>
                        <td class="text-right">{operation['cost_usd']:.2f}</td>
                    </tr>
                """
            
            html += f"""
                    <tr class="total-row">
                        <td colspan="2">Total Operations Cost</td>
                        <td class="text-right">{data['totals']['operations_lkr']:.2f}</td>
                        <td class="text-right">{data['totals']['operations_usd']:.2f}</td>
                    </tr>
                </tbody>
            </table>
            """
        
        # Summary table
        html += f"""
        <h2>Cost Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th class="currency-header">LKR</th>
                    <th class="currency-header">USD</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Components Cost</td>
                    <td class="text-right">{data['totals']['components_lkr']:.2f}</td>
                    <td class="text-right">{data['totals']['components_usd']:.2f}</td>
                </tr>
                <tr>
                    <td>Operations Cost</td>
                    <td class="text-right">{data['totals']['operations_lkr']:.2f}</td>
                    <td class="text-right">{data['totals']['operations_usd']:.2f}</td>
                </tr>
                <tr class="total-row">
                    <td>Total Production Cost</td>
                    <td class="text-right">{data['totals']['total_lkr']:.2f}</td>
                    <td class="text-right">{data['totals']['total_usd']:.2f}</td>
                </tr>
                <tr class="total-row">
                    <td>Unit Cost</td>
                    <td class="text-right">{data['totals']['unit_cost_lkr']:.2f}</td>
                    <td class="text-right">{data['totals']['unit_cost_usd']:.2f}</td>
                </tr>
            </tbody>
        </table>
        
        <p style="margin-top: 30px; color: #6c757d; font-size: 12px;">
            <em>Generated on {fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            Conversion rate: 1 USD = 300 LKR (approximate)</em>
        </p>
        
        </body>
        </html>
        """
        
        return html