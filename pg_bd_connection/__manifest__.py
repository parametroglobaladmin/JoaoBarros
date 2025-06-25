{
    "name": "PG BD Connection",
    "version": "1.0",
    "summary": "Sync invoices between two Odoo databases",
    "description": "Adds a button to replicate invoices to another Odoo 17 database.",
    "author": "Your Name",
    "category": "Accounting",
    "depends": ["account", "sale", "account_reports", "web"],
    "data": [
        "views/account_move_view.xml",
        "views/report_ledger_highlight.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pg_bd_connection/static/src/scss/account_report.scss",
        ],
        "account_reports.assets_pdf_export": [
            "pg_bd_connection/static/src/css/account_report_pdf.css",
        ],
    },
    "installable": True,
    "application": False,
}

