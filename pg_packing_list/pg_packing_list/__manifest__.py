{
    'name': 'Packing List Personalizado',
    'version': '1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Módulo personalizado para gestão de Packing List com cálculo de volumes e peso',
    'description': """
        Módulo Packing List Personalizado
        =================================
        
        Este módulo adiciona funcionalidades avançadas de packing list aos produtos:
        
        * Campos de volume, peso e cubicagem
        * Dimensões dinâmicas (comprimento, altura, largura) para múltiplos volumes
        * Cálculo automático de cubicagem total
        * Interface dinâmica que mostra campos conforme o número de volumes
        * Suporte para até 6 volumes diferentes
        
        Funcionalidades:
        ----------------
        * Campos de dimensão aparecem dinamicamente baseados no número de volumes
        * Cálculo automático de peso total e cubicagem
        * Formatação numérica com 2 casas decimais
        * Interface otimizada para gestão de packing lists
    """,
    'author': 'Parâmetro Global',
    'website': 'https://parametro.global',
    'depends': ['base', 'product', 'stock'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'wizard/cubicagem_wizard_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

