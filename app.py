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
    except:
        return None


@app.post("/extract")
def extract(data: InvoiceInput):

    text = data.invoice_text

    invoice_no = find(
        r"Invoice\s*(?:No|Number)?[:#]?\s*([A-Za-z0-9\-\/]+)",
        text,
    )

    vendor = find(
        r"Vendor[: ]+(.+)",
        text,
    )

    date_text = find(
        r"Date[: ]+(.+)",
        text,
    )

    date = None
    if date_text:
        try:
            date = parser.parse(date_text, dayfirst=True).strftime("%Y-%m-%d")
        except:
            pass

    subtotal = find(
        r"(?:Subtotal|Sub Total)[: ]+Rs\.?\s*([\d,]+\.\d+)",
        text,
    )

    tax = find(
        r"(?:GST.*?|Tax.*?)[: ]+Rs\.?\s*([\d,]+\.\d+)",
        text,
    )

    currency = "INR"

    return {
        "invoice_no": invoice_no,
        "date": date,
        "vendor": vendor,
        "amount": money(subtotal),
        "tax": money(tax),
        "currency": currency,
    }
