from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_order_count = fields.Integer(
        string='Purchase Order Count',
        compute='_compute_purchase_order_count',
        store=True
    )

    mrp_production_count = fields.Integer(
        compute="_compute_mrp_production_count",
        store=True
    )

    @api.depends('state')  # safer: recompute after confirmation, when name is final
    def _compute_purchase_order_count(self):
        for order in self:
            if order.name:
                count = self.env['purchase.order'].search_count([
                    ('origin', '=', order.name)
                ])
                _logger.info("[DEBUG] Found %s POs for sale order %s", count, order.name)
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
            'domain': [('origin', '=', self.name)],
            'context': {'create': False},
        }

    @api.depends('state')  # triggers after confirmation
    def _compute_mrp_production_count(self):
        for order in self:
            if order.name:
                mo_count = self.env['mrp.production'].search_count([
                    ('origin', 'ilike', order.name)
                ])
                _logger.info("[DEBUG] Found %s MOs for sale order %s", mo_count, order.name)
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
            'domain': [('origin', 'ilike', self.name)],
            'context': {'create': False},
        }

