{
    "name": "Sale to Purchase Link",
    "version": "1.0",
    "depends": ["sale", "purchase"],
    "data": [
        "security/ir.model.access.csv",  # ✅ Added this line
        "views/sale_order_views.xml"
    ],
    "installable": True
}

