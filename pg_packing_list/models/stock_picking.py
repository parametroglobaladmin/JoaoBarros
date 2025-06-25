# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Campos totais da entrega
    total_packing_volumes = fields.Float(
        string='Total Volumes',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Total de volumes de todos os produtos na entrega'
    )

    total_packing_weight = fields.Float(
        string='Total Peso (Kg)',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Peso total de todos os produtos na entrega'
    )

    total_packing_cubicagem = fields.Float(
        string='Total Cubicagem',
        digits=(4, 2),
        compute='_compute_packing_totals',
        store=True,
        help='Cubicagem total de todos os produtos na entrega'
    )

    @api.depends('move_ids_without_package.product_id.packing_volumes',
                 'move_ids_without_package.product_id.packing_weight',
                 'move_ids_without_package.product_id.packing_cubicagem',
                 'move_ids_without_package.product_uom_qty')
    def _compute_packing_totals(self):
        """Calcula os totais de packing baseados nos produtos da entrega"""
        for picking in self:
            total_volumes = 0.0
            total_weight = 0.0
            total_cubicagem = 0.0

            for move in picking.move_ids_without_package:
                if move.product_id:
                    qty = move.product_uom_qty
                    total_volumes += move.product_id.packing_volumes * qty
                    total_weight += move.product_id.packing_weight * qty
                    total_cubicagem += move.product_id.packing_cubicagem * qty

            picking.total_packing_volumes = total_volumes
            picking.total_packing_weight = total_weight
            picking.total_packing_cubicagem = total_cubicagem

    def action_open_cubicagem_wizard(self):
        """Abre o wizard de cubicagem geral"""
        return {
            'name': 'Cubicagem Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'cubicagem.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            }
        }


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Campos de packing list por linha de movimento
    move_packing_volumes = fields.Float(
        string='Volumes',
        digits=(4, 2),
        compute='_compute_move_packing',
        store=True,
        help='Volumes para esta linha baseado no produto e quantidade'
    )

    move_packing_weight = fields.Float(
        string='Peso (Kg)',
        digits=(4, 2),
        compute='_compute_move_packing',
        store=True,
        help='Peso para esta linha baseado no produto e quantidade'
    )

    move_packing_cubicagem = fields.Float(
        string='Cubicagem',
        digits=(4, 2),
        compute='_compute_move_packing',
        store=True,
        help='Cubicagem para esta linha baseado no produto e quantidade'
    )

    @api.depends('product_id.packing_volumes',
                 'product_id.packing_weight',
                 'product_id.packing_cubicagem',
                 'product_uom_qty')
    def _compute_move_packing(self):
        """Calcula os valores de packing para cada linha de movimento"""
        for move in self:
            if move.product_id:
                qty = move.product_uom_qty
                move.move_packing_volumes = move.product_id.packing_volumes * qty
                move.move_packing_weight = move.product_id.packing_weight * qty
                move.move_packing_cubicagem = move.product_id.packing_cubicagem * qty
            else:
                move.move_packing_volumes = 0.0
                move.move_packing_weight = 0.0
                move.move_packing_cubicagem = 0.0

    def action_open_move_calc_wizard(self):
        """Abre o wizard de cubicagem para esta linha de stock.move"""
        self.ensure_one()
        return {
            'name': 'Cálculo de Cubicagem da Linha',
            'type': 'ir.actions.act_window',
            'res_model': 'cubicagem.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
            }
        }

