from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_order_count = fields.Integer(
        string="Purchase Order Count",
        compute="_compute_purchase_order_count",
    )

    mrp_production_count = fields.Integer(
        compute="_compute_mrp_production_count",
    )

    @api.depends('procurement_group_id')
    def _compute_purchase_order_count(self):
        """Count purchase orders linked by procurement group."""
        for order in self:
            group = order.procurement_group_id
            if group:
                domain = [('group_id', '=', group.id)]
                count = self.env['purchase.order'].search_count(domain)
                _logger.debug(
                    "Found %s purchase orders for SO %s via group %s",
                    count,
                    order.name,
                    group.id,
                )
                order.purchase_order_count = count
            else:
                order.purchase_order_count = 0

    def action_view_related_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('group_id', '=', self.procurement_group_id.id)],
            'context': {'create': False},
        }

    @api.depends('procurement_group_id')
    def _compute_mrp_production_count(self):
        """Count manufacturing orders linked by procurement group."""
        for order in self:
            group = order.procurement_group_id
            if group:
                domain = [('procurement_group_id', '=', group.id)]
                mo_count = self.env['mrp.production'].search_count(domain)
                _logger.debug(
                    "Found %s manufacturing orders for SO %s via group %s",
                    mo_count,
                    order.name,
                    group.id,
                )
                order.mrp_production_count = mo_count
            else:
                order.mrp_production_count = 0

    def action_view_related_mos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Orders',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('procurement_group_id', '=', self.procurement_group_id.id)],
            'context': {'create': False},
        }

    def action_confirm(self):
        old_names = {order.id: order.name for order in self}
        res = super().action_confirm()
        for order in self:
            old_name = old_names.get(order.id)
            new_name = order.name
            if old_name and new_name and old_name != new_name:
                purchases = self.env['purchase.order'].search([
                    ('origin', '=', old_name)
                ])
                if purchases:
                    purchases.write({'origin': new_name})
        return res

