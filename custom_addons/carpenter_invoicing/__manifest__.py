{
    'name': 'Carpenter Invoicing & Credit Bridge',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Allow paying child invoices with parent credits (Carpenters)',
    'description': """
        This module allows to decouple the billing partner from the paying partner.
        A parent contact (Carpenter) can have balance, and it can be used to reconcile
        the invoices of their child contacts (Final Customers).
        
        Features:
        - Decouple fiscal data (VAT, AFIP responsibility) between parent and child.
        - Cross-partner reconciliation allowed for parent/child relationship.
        - Parent credits available directly on child invoice view.
    """,
    'author': 'Antigravity',
    'depends': ['account', 'l10n_ar'], 
    'data': [
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}
