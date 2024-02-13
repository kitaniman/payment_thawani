# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hmac
import logging
import pprint

from werkzeug.exceptions import Forbidden, Conflict

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)


class ThawaniPayController(http.Controller):
    _success_endpoint = '/payment/thawani/success'
    _cancel_endpoint = '/payment/thawani/cancel'
    _webhook_url = '/payment/thawani/webhook'

    @http.route(_success_endpoint+'/<string:reference>', type='http', auth='public', methods=['GET'])
    def thawani_confirm_checkout(self, **data):
        """ Process the notification data sent by Thawani after redirection.

        :param dict data: The notification data.
        """
        # Don't process the notification data as they contain no valuable information except for the
        # reference and Thawani doesn't expose an endpoint to fetch the data from the API.
        _logger.info("Received a payment confirmation request with data:\n%s", pprint.pformat(data))
        
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'thawani', dict(reference=data['reference'].upper())
        )

        self._verify_payment_status(data, tx_sudo, 'paid')

        tx_sudo._set_done()

        return request.redirect('/payment/status')

    @http.route(_cancel_endpoint+'/<string:reference>', type='http', auth='public', methods=['GET'])
    def thawani_cancel_checkout(self, **data):
        """ Process the notification data sent by Thawani after redirection.

        :param dict data: The notification data.
        """
        # Don't process the notification data as they contain no valuable information except for the
        # reference and Thawani doesn't expose an endpoint to fetch the data from the API.
        _logger.info("Received a pay cancelation request with data:\n%s", pprint.pformat(data))

        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'thawani', dict(reference=data['reference'].upper())
        )

        self._verify_payment_status(data, tx_sudo, 'cancelled')

        tx_sudo._set_canceled()
        
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def thawani_webhook(self, **data):
        """ Process the notification data sent by Thawani to the webhook.

        :param dict data: The notification data.
        :return: The 'OK' string to acknowledge the notification.
        :rtype: str
        """
        _logger.info("Notification received from Thawani with data:\n%s", pprint.pformat(data))
        try:
            # Check the integrity of the notification data.
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'thawani', data
            )
            self._verify_notification_signature(data, tx_sudo)

            # Handle the notification data.
            tx_sudo._handle_notification_data('thawani', data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed.
            _logger.exception("Unable to handle the notification data; skipping to acknowledge.")

        return 'OK'  # Acknowledge the notification.

    @staticmethod
    def _verify_notification_signature(notification_data, tx_sudo):
        """ Check that the received signature matches the expected one.

        :param dict notification_data: The notification data
        :param recordset tx_sudo: The sudoed transaction referenced by the notification data, as a
                                  `payment.transaction` record
        :return: None
        :raise: :class:`werkzeug.exceptions.Forbidden` if the signatures don't match
        """
        received_signature = notification_data.get('secureHash')
        if not received_signature:
            _logger.warning("Received notification with missing signature.")
            raise Forbidden()

        # Compare the received signature with the expected signature computed from the data.
        expected_signature = tx_sudo.provider_id._thawani_calculate_signature(
            notification_data, incoming=True
        )
        if not hmac.compare_digest(received_signature, expected_signature):
            _logger.warning("Received notification with invalid signature.")
            raise Forbidden()
    
    @staticmethod
    def _verify_payment_status(notification_data, tx_sudo, alleged_payment_status):
        session_json = tx_sudo.provider_id._thawani_make_request(
            endpoint='checkout/reference/'+notification_data['reference'].lower(),
            method='GET'
        )
        payment_status = session_json['payment_status']

        if alleged_payment_status != payment_status:
            _logger.warn("The alleged payment status does not match the current payment status.")
            raise Conflict("The alleged payment status does not match the current payment status.")
