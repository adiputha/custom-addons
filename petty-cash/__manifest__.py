{
    "name": "Petty Cash Management",
    "category": "Accounting/Finance",
    "version": "18.0.1.0.0",
    "summary": "Manage petty cash transactions and reports",
    "description": "petty_cash_management_module",
    "author": "ewis",
    "depends": ["base", "account", "web", "mail", "hr", "portal"],
    "external_dependencies": {
        "python": ["pytesseract", "Pillow", "pdf2image"],
        "bin": ["tesseract"],
    },
    "data": [
        # security
        "security/ir.model.access.csv",
        
        # data
        "data/sequence_data.xml",

        # wizard
        "wizard/cash_denomination_wizard_view.xml",
        "wizard/cash_denomination_iou_wizard_view.xml",
        "wizard/initial_denomination_wizard_views.xml",
        
        # views
        "views/cash_reimbursement_views.xml",
        
        "views/float_customization_views.xml",
        "views/float_request_views.xml",
        "views/float_denomination_views.xml",
        
        "views/iou_request_views.xml",
        "views/iou_request_list_views.xml",
        
        "views/petty_cash_list_views.xml",
        "views/petty_cash_bill_settlement_views.xml",
        "views/petty_cash_category_views.xml",
        "views/petty_cash_request_views.xml",
        
        
        "views/petty_cash_menu.xml",
        
        #reports
        "report/petty_cash_report_template.xml",
        "report/reimbursement_report_template.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "petty-cash/static/src/css/float_kanban.css",
        ]
    },
    "qweb": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
