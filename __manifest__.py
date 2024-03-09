# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Payment Provider: Thawani",
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A payment provider based in Oman covering most Omani payment methods.",
    'description': " ",  # Non-empty string to avoid loading the README file.
    'depends': ['payment'],
    'data': [
        'views/payment_thawani_templates.xml',
        'views/payment_provider_views.xml',
        
        'data/payment_provider_data.xml'
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
