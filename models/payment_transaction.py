# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from werkzeug.urls import url_join

from odoo import _, api, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_thawani.controllers.main import ThawaniPayController


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of `payment` to return Thawani-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`.

        :param dict processing_values: The generic and specific processing values of the
                                       transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        self.ensure_one()

        base_url = self.provider_id.get_base_url()

        session_json = self.provider_id._thawani_make_request(
            endpoint='checkout/session',
            json={
                "client_reference_id": processing_values['reference'],
                "mode": "payment",
                "products": [
                    {
                        "name": "O50",
                        "quantity": 1,
                        "unit_amount": int(processing_values['amount']*1000)
                    }
                ],
                "success_url": url_join(base=base_url, url=ThawaniPayController._return_url),
                "cancel_url": url_join(base=base_url, url=ThawaniPayController._return_url)
            },
            method='POST'
        )

        session_id = session_json['data']['session_id']

        payment_page_url = url_join(
            base=self.provider_id._thawani_get_payment_page_url(),
            url=session_id
        )

        rendering_values = {
            'session_url': payment_page_url,
            'key': self.provider_id.thawani_publishable_key
        }
        return rendering_values
