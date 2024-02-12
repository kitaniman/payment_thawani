# Part of Odoo. See LICENSE file for full copyright and licensing details.

SUPPORTED_CURRENCIES = {
    'OMR'
}

PROVIDER_ADDRESSES = {
    'production': 'https://checkout.thawani.om',
    'test': 'https://uatcheckout.thawani.om'
}

DEFAULT_PAYMENT_METHODS = [
    # Primary payment methods.
    'card',
    # Brand payment methods.
    'visa',
    'mastercard',
    'amex'
]