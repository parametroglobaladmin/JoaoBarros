# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CubicagemWizard(models.TransientModel):
    _name = 'cubicagem.wizard'
    _description = 'Assistente de Cálculo de Cubicagem'

    picking_id = fields.Many2one('stock.picking', string='Entrega')
    move_id = fields.Many2one('stock.move', string='Linha do Produto')
    sale_order_id = fields.Many2one('sale.order', string='Ordem de Venda')
    sale_line_id = fields.Many2one('sale.order.line', string='Linha da Venda')

    volumes = fields.Float(string='Volumes', digits=(4, 2), default=0.0)

    comprimento_1 = fields.Float(string='Comprimento 1', digits=(4, 2), default=0.0)
    altura_1 = fields.Float(string='Altura 1', digits=(4, 2), default=0.0)
    largura_1 = fields.Float(string='Largura 1', digits=(4, 2), default=0.0)

    comprimento_2 = fields.Float(string='Comprimento 2', digits=(4, 2), default=0.0)
    altura_2 = fields.Float(string='Altura 2', digits=(4, 2), default=0.0)
    largura_2 = fields.Float(string='Largura 2', digits=(4, 2), default=0.0)

    comprimento_3 = fields.Float(string='Comprimento 3', digits=(4, 2), default=0.0)
    altura_3 = fields.Float(string='Altura 3', digits=(4, 2), default=0.0)
    largura_3 = fields.Float(string='Largura 3', digits=(4, 2), default=0.0)

    comprimento_4 = fields.Float(string='Comprimento 4', digits=(4, 2), default=0.0)
    altura_4 = fields.Float(string='Altura 4', digits=(4, 2), default=0.0)
    largura_4 = fields.Float(string='Largura 4', digits=(4, 2), default=0.0)

    comprimento_5 = fields.Float(string='Comprimento 5', digits=(4, 2), default=0.0)
    altura_5 = fields.Float(string='Altura 5', digits=(4, 2), default=0.0)
    largura_5 = fields.Float(string='Largura 5', digits=(4, 2), default=0.0)

    comprimento_6 = fields.Float(string='Comprimento 6', digits=(4, 2), default=0.0)
    altura_6 = fields.Float(string='Altura 6', digits=(4, 2), default=0.0)
    largura_6 = fields.Float(string='Largura 6', digits=(4, 2), default=0.0)

    cubicagem_total = fields.Float(
        string='Cubicagem Total',
        digits=(4, 2),
        compute='_compute_cubicagem_total',
        store=True
    )

    peso_estimado = fields.Float(
        string='Peso Estimado (Kg)',
        digits=(4, 2),
        readonly=True
    )

    # Campos para peso manual
    peso_manual = fields.Boolean(
        string='Peso Manual',
        default=False,
        help='Ativar para introduzir peso manualmente em vez de usar cálculo automático'
    )
    
    peso_manual_valor = fields.Float(
        string='Peso Manual (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso introduzido manualmente'
    )

    @api.depends('volumes', 'comprimento_1', 'altura_1', 'largura_1',
                 'comprimento_2', 'altura_2', 'largura_2',
                 'comprimento_3', 'altura_3', 'largura_3',
                 'comprimento_4', 'altura_4', 'largura_4',
                 'comprimento_5', 'altura_5', 'largura_5',
                 'comprimento_6', 'altura_6', 'largura_6')
    def _compute_cubicagem_total(self):
        for wizard in self:
            total = 0.0
            dims = [
                (wizard.comprimento_1, wizard.altura_1, wizard.largura_1),
                (wizard.comprimento_2, wizard.altura_2, wizard.largura_2),
                (wizard.comprimento_3, wizard.altura_3, wizard.largura_3),
                (wizard.comprimento_4, wizard.altura_4, wizard.largura_4),
                (wizard.comprimento_5, wizard.altura_5, wizard.largura_5),
                (wizard.comprimento_6, wizard.altura_6, wizard.largura_6),
            ]
            for i in range(int(min(6, wizard.volumes))):
                c, a, l = dims[i]
                total += c * a * l
            wizard.cubicagem_total = total

    def action_calcular(self):
        self.ensure_one()
        if not (self.move_id or self.sale_line_id):
            raise ValidationError("Linha do produto não encontrada.")

        # Validações adicionais
        if self.peso_manual and self.peso_manual_valor <= 0:
            raise ValidationError("O peso manual deve ser maior que zero.")

        # Determinar o peso a usar
        if self.peso_manual:
            # Usar peso manual se checkbox estiver ativada
            peso_final = self.peso_manual_valor
            self.peso_estimado = peso_final
        else:
            # Usar cálculo automático baseado na cubicagem
            peso_estimado = self.cubicagem_total * 80
            self.peso_estimado = peso_estimado
            peso_final = peso_estimado

        # Atualizar a linha do stock.move se existir
        if self.move_id:
            self.move_id.write({
                'move_packing_volumes': self.volumes,
                'move_packing_cubicagem': self.cubicagem_total,
                'move_packing_weight': peso_final
            })

        # Atualizar a linha do sale.order se existir
        if self.sale_line_id:
            self.sale_line_id.write({
                'line_packing_volumes': self.volumes,
                'line_packing_cubicagem': self.cubicagem_total,
                'line_packing_weight': peso_final
            })

        return {'type': 'ir.actions.act_window_close'}  # <== FECHA imediatamente o wizard

    def action_cancelar(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        move_id = self.env.context.get('default_move_id')
        if move_id:
            move = self.env['stock.move'].browse(move_id)
            res.update({
                'move_id': move.id,
                'volumes': move.move_packing_volumes,
                'peso_estimado': move.move_packing_weight,
                'cubicagem_total': move.move_packing_cubicagem,
                'peso_manual': False,  # Por defeito, peso manual desativado
                'peso_manual_valor': move.move_packing_weight,  # Valor atual como referência
            })
        sale_line_id = self.env.context.get('default_sale_line_id')
        if sale_line_id:
            line = self.env['sale.order.line'].browse(sale_line_id)
            res.update({
                'sale_line_id': line.id,
                'volumes': line.line_packing_volumes,
                'peso_estimado': line.line_packing_weight,
                'cubicagem_total': line.line_packing_cubicagem,
                'peso_manual': False,
                'peso_manual_valor': line.line_packing_weight,
            })
        return res
