from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dateutil import parser
import re

app = FastAPI()

# Enable CORS
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
    currency: str | None = None


def find(pattern, text, flags=re.IGNORECASE):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def money(value):
    if value is None:
        return None

    value = value.replace(",", "")
    value = re.sub(r"[^\d.]", "", value)

    try:
        return float(value)
    except ValueError:
        return None


@app.post("/extract", response_model=InvoiceOutput)
def extract(data: InvoiceInput):

    text = data.invoice_text

    # Invoice Number
    invoice_no = find(
        r"(?:Invoice(?:\s*(?:No|Number|#))?|Inv(?:oice)?\s*#?)\s*[:#-]?\s*([A-Za-z0-9\-/]+)",
        text,
    )

    # Vendor
    vendor = find(
        r"(?:Vendor(?:\s+Name)?|Supplier(?:\s+Name)?|Seller|Sold\s*By|From)\s*[:\-]?\s*(.+)",
        text,
    )

    # Date
    date_text = find(
        r"(?:Invoice\s*Date|Date)\s*[:\-]?\s*(.+)",
        text,
    )

    date = None
    if date_text:
        try:
            date = parser.parse(date_text, dayfirst=True).strftime("%Y-%m-%d")
        except Exception:
            date = None

    # Subtotal / Amount Before Tax
    subtotal = find(
        r"(?:Subtotal|Sub\s*Total|Amount\s*Before\s*Tax|Net\s*Amount)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)",
        text,
    )

    # Tax
    tax = find(
        r"(?:GST.*?|CGST.*?|SGST.*?|IGST.*?|Tax.*?)\s*[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)",
        text,
    )

    return {
        "invoice_no": invoice_no,
        "date": date,
        "vendor": vendor,
        "amount": money(subtotal),
        "tax": money(tax),
        "currency": "INR",
    }
