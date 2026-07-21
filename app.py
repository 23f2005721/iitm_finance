from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dateutil import parser
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceInput(BaseModel):
    invoice_text: str


class InvoiceOutput(BaseModel):
    invoice_no: str | None = None
    date: str | None = None
    vendor: str | None = None
    amount: float | None = None
    tax: float | None = None
    currency: str | None = "INR"


def money(value):
    if value is None:
        return None
    value = value.replace(",", "")
    value = re.sub(r"[^\d.]", "", value)
    try:
        return float(value)
    except Exception:
        return None


@app.post("/extract", response_model=InvoiceOutput)
def extract(data: InvoiceInput):

    invoice_no = None
    vendor = None
    date = None
    amount = None
    tax = None

    lines = [l.strip() for l in data.invoice_text.splitlines() if l.strip()]

    for line in lines:
        low = line.lower()

        # Invoice Number
        if invoice_no is None and any(x in low for x in [
            "invoice no", "invoice number", "invoice#", "invoice #", "inv no", "inv#"
        ]):
            if ":" in line:
                invoice_no = line.split(":", 1)[1].strip()
            else:
                m = re.search(r"([A-Za-z0-9\-/]+)$", line)
                if m:
                    invoice_no = m.group(1)

        # Vendor
        if vendor is None and any(x in low for x in [
            "vendor", "vendor name", "supplier", "supplier name",
            "seller", "sold by", "company", "from"
        ]):
            if ":" in line:
                vendor = line.split(":", 1)[1].strip()

        # Date
        if date is None and "date" in low:
            if ":" in line:
                try:
                    dt = parser.parse(line.split(":", 1)[1].strip(), dayfirst=True)
                    date = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass

        # Amount before tax
        if amount is None and any(x in low for x in [
            "subtotal", "sub total", "amount before tax", "net amount"
        ]):
            nums = re.findall(r"[\d,]+(?:\.\d+)?", line)
            if nums:
                amount = money(nums[-1])

        # Tax
        if tax is None and any(x in low for x in [
            "gst", "cgst", "sgst", "igst", "tax"
        ]):
            nums = re.findall(r"[\d,]+(?:\.\d+)?", line)
            if nums:
                tax = money(nums[-1])

    return {
        "invoice_no": invoice_no,
        "date": date,
        "vendor": vendor,
        "amount": amount,
        "tax": tax,
        "currency": "INR",
    }
