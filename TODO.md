# UI Modernization TODO

## Steps
1. [x] Rewrite `templates/index.html` with modern SaaS UI (Lucide icons, sidebar, stat cards, tables, modals, finance tabs, chat)
2. [x] Update `templates/login.html` to match modern theme
3. [x] Update `templates/invoice_detail.html` to match modern theme
4. [x] Update `templates/vendors.html` to match modern theme
5. [x] Mount static files in `main.py`
6. [x] Smoke test by running the FastAPI server — all endpoints returning 200 OK

---

# Incoming/Outgoing Invoice Feature TODO

## Steps
1. [x] `models/schemas.py` — Add `invoice_type` field to Invoice model
2. [x] `tools/invoice.py` — Store `invoice_type`, derive category, return in getters
3. [x] `services/invoice_service.py` — Pass `invoice_type` through to `create_invoice`
4. [x] `routes/invoice_routes.py` — Accept `invoice_type` on upload, return type/category
5. [x] `tools/bookkeeping.py` — Include invoices in `get_summary()` totals
6. [x] `tools/vendors.py` — Include `invoice_type` in vendor detail invoice list
7. [x] `templates/index.html` — Add type selector + Type column in invoice table
8. [x] `static/js/dashboard.js` — Send type on upload, render type column, update panel
9. [x] `templates/invoice_detail.html` — Show invoice type and category
10. [x] Test & verify dashboard summary, upload flow, and detail pages

