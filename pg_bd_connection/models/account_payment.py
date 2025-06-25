import logging
import odoo
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_sync_payment(self):
        """
        Sync payment with another Odoo database by matching invoices via the ref field
        and calling action_register_payment on the correct invoice.
        """
        _logger.info(" Starting payment synchronization for Payment ID: %s", self.id)

        second_db = "PICCOLO_COMMUNITY"
        fixed_journal_id = 14  # ✅ Always apply Journal ID 14 in second database

        try:
            registry = odoo.registry(second_db)
            if not registry:
                raise ValueError(f"❌ Registry for database {second_db} not found!")

            with registry.cursor() as cr:
                second_env = api.Environment(cr, self.env.uid, {})

                #  Force access to all companies in second DB
                companies = second_env["res.company"].sudo().search([]).ids
                second_env = api.Environment(cr, self.env.uid, {
                    "allowed_company_ids": companies,
                    "force_company": companies[0],
                })

                _logger.info("✅ Successfully switched to database: %s", second_db)

                # ---- 1. Ensure Customer Exists ----
                customer = second_env["res.partner"].sudo().search(
                    [("name", "=", self.partner_id.name)], limit=1
                )

                if not customer:
                    _logger.info(" Customer not found. Creating new customer: %s", self.partner_id.name)
                    customer = second_env["res.partner"].sudo().create({
                        "name": self.partner_id.name,
                        "email": self.partner_id.email,
                        "phone": self.partner_id.phone,
                        "street": self.partner_id.street,
                        "city": self.partner_id.city,
                        "zip": self.partner_id.zip,
                        "country_id": self.partner_id.country_id.id if self.partner_id.country_id else False,
                        "vat": self.partner_id.vat,
                        "customer_rank": 1,
                    })
                    _logger.info("✅ New customer created: ID %s", customer.id)

                # ---- 2. Find the Correct Invoice ----
                invoice = None
                if self.ref:
                    _logger.info(" Searching for invoice in second database with name matching ref: %s", self.ref)
                    invoice = second_env["account.move"].sudo().search([("name", "=", self.ref)], limit=1)

                if not invoice:
                    raise ValueError(f"❌ No matching invoice found in second database with name: {self.ref}")

                # ✅ Ensure Invoice is Confirmed
                if invoice.state != "posted":
                    raise ValueError(f"❌ Invoice {invoice.name} is not confirmed in second database!")

                # ---- 3. Prepare Payment Data ----
                _logger.info("✅ Invoice found and confirmed. Preparing payment data...")

                # Match payment method
                payment_method_name = self.payment_method_line_id.name if self.payment_method_line_id else None
                payment_method_line = None

                if payment_method_name:
                    _logger.info(" Searching for Payment Method in second database: %s", payment_method_name)
                    payment_method_line = second_env["account.payment.method.line"].sudo().search(
                        [("name", "=", payment_method_name)], limit=1
                    )

                if not payment_method_line:
                    _logger.warning("⚠ Payment method not found in second database. Using default method.")
                    payment_method_line = second_env["account.payment.method.line"].sudo().search([], limit=1)

                if not payment_method_line:
                    raise ValueError("❌ No available payment method found in second database!")

                # ---- 4. Register Payment via `action_register_payment` ----
                payment_vals = {
                    "amount": self.amount,
                    "payment_date": self.date,
                    "journal_id": fixed_journal_id,  # ✅ Always use fixed journal 14
                    "payment_method_line_id": payment_method_line.id,
                    "payment_type": self.payment_type,
                    "partner_type": self.partner_type,
                    "partner_id": customer.id,
                    "currency_id": self.currency_id.id,
                }

                # ✅ Call `action_register_payment` on the invoice
                _logger.info("✅ Registering payment for invoice: %s", invoice.name)
                payment_wizard = second_env["account.payment.register"].with_context(
                    active_model="account.move",
                    active_ids=invoice.ids,
                ).create(payment_vals)

                # ✅ Execute the payment
                payment_wizard.action_create_payments()
                _logger.info("✅ Payment successfully registered for invoice %s", invoice.name)

                # ✅ Mark as Synced
                self.sudo().write({"x_studio_community_1": True})
                _logger.info("✅ Invoice marked as synced (x_studio_community = True)")

                self.message_post(body=_("✅ Payment successfully synced."))
                return True

        except Exception as e:
            _logger.error("❌ Failed to register payment in second database: %s", str(e))
            raise ValueError(_("Failed to sync payment: %s") % str(e))

    def mark_as_sent(self):
        """Marks payment as sent and reconciles it with the invoice if possible, else marks the invoice as paid."""
        for payment in self:
            _logger.info(f"Processing payment: {payment.name} (State: {payment.state})")

            # Ensure payment is in the correct state
            if payment.state != 'posted':
                _logger.warning(f"Skipping payment {payment.name}: Not posted.")
                continue
            if payment.is_move_sent:
                _logger.warning(f"Skipping payment {payment.name}: Already marked as sent.")
                continue
            if payment.payment_method_code != 'manual':
                _logger.warning(f"Skipping payment {payment.name}: Payment method is not 'manual'.")
                continue

            # Find the invoice using the ref field
            invoice = self.env['account.move'].search([
                ('name', '=', payment.ref),
                ('state', '=', 'posted'),
                ('move_type', 'in', ['out_invoice', 'in_invoice'])
            ], limit=1)

            if not invoice:
                _logger.warning(f"Payment {payment.name}: No matching invoice found for ref '{payment.ref}'.")
                continue
            
            _logger.info(f"Found invoice: {invoice.name} (State: {invoice.state}, Payment State: {invoice.payment_state})")

            # Get reconciliable move lines
            payment_move_lines = payment.move_id.line_ids.filtered(lambda l: l.account_id.reconcile and not l.reconciled)
            invoice_move_lines = invoice.line_ids.filtered(lambda l: l.account_id.reconcile and not l.reconciled)

            _logger.info(f"Payment move lines count: {len(payment_move_lines)}")
            _logger.info(f"Invoice move lines count: {len(invoice_move_lines)}")

            if not invoice_move_lines:
                _logger.warning(f"No valid invoice move lines found for invoice {invoice.name}. Marking as paid manually.")

                # Forcefully mark the invoice as paid
                invoice.payment_state = 'paid'
                _logger.info(f"Invoice {invoice.name} manually marked as paid.")

            elif payment_move_lines:
                try:
                    _logger.info(f"Attempting to reconcile payment {payment.name} with invoice {invoice.name}...")
                    (invoice_move_lines + payment_move_lines).reconcile()
                    _logger.info(f"Reconciliation successful for payment {payment.name} and invoice {invoice.name}.")
                except Exception as e:
                    _logger.error(f"Reconciliation failed for payment {payment.name} - Invoice {invoice.name}: {str(e)}")

            # Mark the payment as sent
            payment.is_move_sent = True
            _logger.info(f"Payment {payment.name} marked as sent.")
