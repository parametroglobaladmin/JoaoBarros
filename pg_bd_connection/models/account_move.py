import logging
import odoo
from psycopg2 import sql
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


def _ensure_column(env, table, column, column_def):
    """Ensure a column exists in the given table."""
    env.cr.execute(
        """SELECT 1 FROM information_schema.columns
            WHERE table_name=%s AND column_name=%s""",
        (table, column),
    )
    if not env.cr.fetchone():
        _logger.warning("Column %s.%s missing. Creating it.", table, column)
        env.cr.execute(
            sql.SQL("ALTER TABLE {} ADD COLUMN {} {}")
            .format(sql.Identifier(table), sql.Identifier(column), sql.SQL(column_def))
        )
        env.cr.commit()

class AccountMove(models.Model):
    _inherit = "account.move"

    x_original_invoice_id = fields.Integer(string="Original Invoice ID", copy=False)  # ✅ Ensure field exists

    def action_sync_invoice(self):
        """
        Sync invoice with another Odoo database and confirm the invoice in the first database if not confirmed yet.
        """
        _logger.info("🔄 Starting invoice synchronization for Invoice ID: %s", self.id)

        # Define the first and second database names
        first_db = "PICCOLO"
        second_db = "PICCOLO_COMMUNITY"

        # ✅ Ensure Invoice is Updated & Confirmed in the First Database
        try:
            registry = odoo.registry(first_db)
            if not registry:
                raise ValueError(f"❌ Registry for database {first_db} not found!")

            with registry.cursor() as cr:
                first_env = api.Environment(cr, self.env.uid, {})

                # 🔍 Search for the original invoice in the first database
                original_invoice = first_env["account.move"].sudo().search([("id", "=", self.id)], limit=1)

                if not original_invoice:
                    raise ValueError(f"❌ No matching invoice found in first database for ID {self.id}")

                # ✅ Change Journal ID First (Before Confirming)
                _logger.info("🔄 Changing journal_id to 50 in first database...")
                original_invoice.sudo().write({"journal_id": 50})
                cr.commit()
                _logger.info("✅ journal_id successfully changed to 50.")

                # ✅ If the invoice is not posted, confirm it
                if original_invoice.state != "posted":
                    _logger.info("✅ Confirming invoice in first database: %s", original_invoice.id)
                    original_invoice.sudo().action_post()
                    cr.commit()
                    _logger.info("✅ Invoice successfully confirmed in first database.")

        except Exception as e:
            _logger.error("❌ Failed to confirm invoice in first database: %s", str(e))
            raise ValueError(_("Could not confirm invoice in first database: %s") % str(e))

        # ✅ Proceed with syncing the invoice to the second database
        try:
            registry = odoo.registry(second_db)
            if not registry:
                raise ValueError(f"❌ Registry for database {second_db} not found!")

            with registry.cursor() as cr:
                second_env = api.Environment(cr, self.env.uid, {})

                # 🔹 Force access to all companies
                companies = second_env["res.company"].sudo().search([]).ids
                if not companies:
                    raise ValueError(f"❌ No companies found in database {second_db}")

                second_env = api.Environment(cr, self.env.uid, {
                    "allowed_company_ids": companies,
                    "force_company": companies[0],
                })

                _logger.info("✅ Successfully switched to database: %s with full company access", second_db)

                # 🔹 Assign company access
                second_env.user_id = second_env["res.users"].browse(self.env.uid).sudo()
                second_env.user_id.sudo().write({
                    "company_ids": [(6, 0, companies)],
                    "company_id": companies[0],
                })

                # Ensure required columns exist
                _ensure_column(second_env, "account_move", "delivery_count", "INTEGER DEFAULT 0")

                # ---- 1. Ensure Customer Exists ----
                customer = second_env["res.partner"].sudo().search([("name", "=", self.partner_id.name)], limit=1)

                if not customer:
                    _logger.info("🔄 Customer not found. Creating new customer: %s", self.partner_id.name)
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

                # ---- 2. Ensure Journal Exists ----
                journal = second_env["account.journal"].sudo().search([("type", "=", "sale")], limit=1)
                if not journal:
                    raise ValueError("❌ No sales journal found in second database!")

                if not journal.default_account_id:
                    raise ValueError(f"❌ Journal {journal.name} does not have a default account assigned!")

                account_id = journal.default_account_id.id

                # ---- 3. Ensure Invoice Lines in Correct Order ----
                invoice_lines = []
                for line in self.invoice_line_ids.sorted(lambda l: l.sequence):
                    if line.display_type in ["line_section", "line_note"]:
                        invoice_lines.append((0, 0, {
                            "display_type": line.display_type,
                            "name": line.name,
                            "sequence": line.sequence,
                        }))
                        continue

                    tax_ids = [
                        second_env["account.tax"].sudo().search([("name", "=", tax.name)], limit=1).id
                        for tax in line.tax_ids
                        if second_env["account.tax"].sudo().search([("name", "=", tax.name)], limit=1)
                    ]

                    invoice_lines.append((0, 0, {
                        "name": line.name,
                        "quantity": line.quantity or 0.0,
                        "price_unit": line.price_unit or 0.0,
                        "discount": line.discount or 0.0,
                        "tax_ids": [(6, 0, tax_ids)] if tax_ids else [],
                        "account_id": account_id,
                        "sequence": line.sequence,
                    }))

                invoice_data = {
                    "partner_id": customer.id,
                    "move_type": self.move_type,
                    "invoice_date": self.invoice_date,
                    "invoice_date_due": self.invoice_date_due,
                    "payment_reference": self.payment_reference,
                    "state": "draft",
                    "invoice_line_ids": invoice_lines,
                    "journal_id": journal.id,
                }

                # ✅ Check if `x_original_invoice_id` Exists in the 2nd Database Before Using
                if "x_original_invoice_id" in second_env["account.move"]._fields:
                    invoice_data["x_original_invoice_id"] = self.id

                try:
                    new_invoice = second_env["account.move"].sudo().create(invoice_data)
                    _logger.info("✅ Invoice successfully created in the second database: ID %s", new_invoice.id)

                    # ✅ Mark as Synced
                    self.sudo().write({"x_studio_community": True})
                    _logger.info("✅ Invoice marked as synced (x_studio_community = True)")

                    self.message_post(body=_("✅ Invoice successfully synced."))
                    return True
                except Exception as e:
                    _logger.error("❌ Failed to create invoice in the second database: %s", str(e))
                    raise ValueError(_("Failed to create invoice in the second database: %s") % str(e))

        except Exception as e:
            _logger.error("❌ Failed to switch to second database: %s", str(e))
            raise ValueError(_("Could not access the second database: %s") % str(e))

