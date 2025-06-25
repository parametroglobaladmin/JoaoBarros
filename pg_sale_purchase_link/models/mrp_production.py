from odoo import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            record._update_procurement_group_from_sale()
        return records

    def _update_procurement_group_from_sale(self):
        for production in self:
            if not production.origin:
                continue
            sale_order = self.env['sale.order'].search([
                ('name', '=', production.origin)
            ], limit=1)
            if sale_order:
                production.procurement_group_id = sale_order.procurement_group_id.id

