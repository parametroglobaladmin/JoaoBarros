{
    "name": "Sale to Purchase Link",
    "version": "1.0",
    # ensure procurement_group_id exists and MRP models are available
    "depends": ["sale", "purchase", "sale_stock", "mrp"],
    "data": [
        "security/ir.model.access.csv",  # ✅ Added this line
        "views/sale_order_views.xml"
    ],
    "installable": True
}

