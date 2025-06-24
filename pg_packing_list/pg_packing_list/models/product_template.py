# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos principais da packing list
    packing_volumes = fields.Float(
        string='Volumes',
        digits=(4, 2),
        default=0.0,
        help='Número de volumes para este produto'
    )

    packing_weight = fields.Float(
        string='Peso (Kg)',
        digits=(4, 2),
        default=0.0,
        help='Peso total em quilogramas'
    )

    packing_cubicagem = fields.Float(
        string='Cubicagem',
        digits=(4, 2),
        default=0.0,
        help='Cubicagem total em m³ (informada manualmente)'
    )

    # Dimensões do primeiro volume (sempre visível)
    packing_comprimento = fields.Float(string='Comprimento', digits=(4, 2), default=0.0)
    packing_altura = fields.Float(string='Altura', digits=(4, 2), default=0.0)
    packing_largura = fields.Float(string='Largura', digits=(4, 2), default=0.0)

    # Volume 2
    packing_comprimento_2 = fields.Float(string='Comprimento 2', digits=(4, 2), default=0.0)
    packing_altura_2 = fields.Float(string='Altura 2', digits=(4, 2), default=0.0)
    packing_largura_2 = fields.Float(string='Largura 2', digits=(4, 2), default=0.0)

    # Volume 3
    packing_comprimento_3 = fields.Float(string='Comprimento 3', digits=(4, 2), default=0.0)
    packing_altura_3 = fields.Float(string='Altura 3', digits=(4, 2), default=0.0)
    packing_largura_3 = fields.Float(string='Largura 3', digits=(4, 2), default=0.0)

    # Volume 4
    packing_comprimento_4 = fields.Float(string='Comprimento 4', digits=(4, 2), default=0.0)
    packing_altura_4 = fields.Float(string='Altura 4', digits=(4, 2), default=0.0)
    packing_largura_4 = fields.Float(string='Largura 4', digits=(4, 2), default=0.0)

    # Volume 5
    packing_comprimento_5 = fields.Float(string='Comprimento 5', digits=(4, 2), default=0.0)
    packing_altura_5 = fields.Float(string='Altura 5', digits=(4, 2), default=0.0)
    packing_largura_5 = fields.Float(string='Largura 5', digits=(4, 2), default=0.0)

    # Volume 6
    packing_comprimento_6 = fields.Float(string='Comprimento 6', digits=(4, 2), default=0.0)
    packing_altura_6 = fields.Float(string='Altura 6', digits=(4, 2), default=0.0)
    packing_largura_6 = fields.Float(string='Largura 6', digits=(4, 2), default=0.0)

    # Validações

    @api.constrains('packing_volumes')
    def _check_volumes_range(self):
        for record in self:
            if record.packing_volumes < 0:
                raise ValidationError("O número de volumes não pode ser negativo.")
            if record.packing_volumes > 6:
                raise ValidationError("O número máximo de volumes suportado é 6.")

    @api.constrains('packing_weight')
    def _check_weight_positive(self):
        for record in self:
            if record.packing_weight < 0:
                raise ValidationError("O peso não pode ser negativo.")

    @api.constrains('packing_comprimento', 'packing_altura', 'packing_largura',
                    'packing_comprimento_2', 'packing_altura_2', 'packing_largura_2',
                    'packing_comprimento_3', 'packing_altura_3', 'packing_largura_3',
                    'packing_comprimento_4', 'packing_altura_4', 'packing_largura_4',
                    'packing_comprimento_5', 'packing_altura_5', 'packing_largura_5',
                    'packing_comprimento_6', 'packing_altura_6', 'packing_largura_6')
    def _check_dimensions_positive(self):
        for record in self:
            dimension_fields = [
                'packing_comprimento', 'packing_altura', 'packing_largura',
                'packing_comprimento_2', 'packing_altura_2', 'packing_largura_2',
                'packing_comprimento_3', 'packing_altura_3', 'packing_largura_3',
                'packing_comprimento_4', 'packing_altura_4', 'packing_largura_4',
                'packing_comprimento_5', 'packing_altura_5', 'packing_largura_5',
                'packing_comprimento_6', 'packing_altura_6', 'packing_largura_6'
            ]
            for field_name in dimension_fields:
                if getattr(record, field_name, 0.0) < 0:
                    raise ValidationError(
                        f"A dimensão '{record._fields[field_name].string}' não pode ser negativa."
                    )
