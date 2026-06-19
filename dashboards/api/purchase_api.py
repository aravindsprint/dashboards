"""
Purchase Dashboard API  —  stub / template
==========================================
Follow this pattern when building the Purchase Dashboard.
Each new dashboard gets its own *_api.py file here.
"""
import frappe
from frappe.utils import nowdate, add_months, flt


@frappe.whitelist()
def get_purchase_summary(from_date=None, to_date=None, company=None):
    """TODO: KPIs for Purchase Invoice + Purchase Order"""
    raise NotImplementedError("Purchase Dashboard coming soon")


@frappe.whitelist()
def get_supplier_wise(from_date=None, to_date=None, company=None, limit=15):
    """TODO: Top suppliers by spend"""
    raise NotImplementedError("Purchase Dashboard coming soon")


@frappe.whitelist()
def get_pending_grn(company=None):
    """TODO: Purchase Orders with pending GRN"""
    raise NotImplementedError("Purchase Dashboard coming soon")
