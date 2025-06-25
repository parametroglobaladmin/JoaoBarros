from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_line_description = fields.Char(
        string="Descrição do Produto",
        compute="_compute_order_line_description",
        store=False,
        search="_search_order_line_description"
    )

    def _compute_order_line_description(self):
        """Concatenates all order line names into a single field"""
        for order in self:
            order.order_line_description = ", ".join(order.order_line.mapped("name"))

    def _search_order_line_description(self, operator, value):
        """Searches for sale orders containing a description in their sale order lines"""
        orders = self.env['sale.order.line'].search([('name', 'ilike', value)]).mapped('order_id')
        return [('id', 'in', orders.ids)]

