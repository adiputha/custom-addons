{
    'name': 'Multi Currency Support',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Display MO Overview in both LKR and USD currencies',
    
    'description': """This module adds multi-currency support to the
        Manufacturing Orders (MO) by allowing users to 
        view and manage MO data in both LKR and USD currencies.""",
    
    'author': 'Ewis',
    'depends': ['mrp', 'base'],
    
    'data': [
        # 'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        
        'report/report_actions.xml',
        'report/mrp_report_mo_overview_dual.xml',
    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
}