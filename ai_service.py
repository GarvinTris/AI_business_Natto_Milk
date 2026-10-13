import json
import os

from dotenv import load_dotenv
from google import genai

from schemas import OrderAnalysis


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)


# ============================================================
# ANALYZE ORDER
# ============================================================

def analyze_order(
    message: str,
    api_key: str,
    product_catalog: dict,
    product_categories: dict,
    model_name: str,
    reference_date: str,
):

    if not api_key:
        raise ValueError(
            "Gemini API Key belum diisi."
        )

    if not message or not message.strip():
        raise ValueError(
            "Pesan customer kosong."
        )

    # ========================================================
    # PRODUCT CATALOG
    # ========================================================

    catalog_text = "\n".join(
        f"- {product}: Rp{price}"
        for product, price
        in product_catalog.items()
    )

    # ========================================================
    # PRODUCT CATEGORIES
    # ========================================================

    category_lines = []

    for category, products in product_categories.items():

        product_list = ", ".join(products)

        category_lines.append(
            f"- {category}: {product_list}"
        )

    category_text = "\n".join(
        category_lines
    )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are an order understanding assistant for an Indonesian
coffee shop.

Your job is ONLY to understand the customer's message and
convert it into structured order information.

Do NOT calculate prices.

Do NOT invent products.

Do NOT invent quantities.

Do NOT invent addresses.

Do NOT invent dates or times.

If information is missing or ambiguous, leave the field
empty/null and identify it in missing_fields.

REFERENCE DATE:
{reference_date}

============================================================
PRODUCT CATALOG
============================================================

{catalog_text}

============================================================
PRODUCT CATEGORIES
============================================================

{category_text}

============================================================
IMPORTANT RULES
============================================================

1. Match products to the catalog whenever possible.

2. If the customer uses natural language such as:
   - satu
   - dua
   - tiga
   - empat
   - lima

   convert them into numeric quantities.

3. Understand relative dates such as:
   - hari ini
   - besok
   - lusa
   - Jumat
   - minggu depan

   based on the reference date.

4. Understand natural-language times such as:
   - jam lima
   - jam 5 sore
   - jam 10 pagi
   - nanti siang

5. Do not assume that an informal product name is a catalog
   product unless there is a reasonable match.

6. If a product cannot be matched confidently, keep the
   product_name as the customer's wording and let the
   business rules validate it later.

7. fulfillment must be one of:
   - dine_in
   - takeaway
   - delivery
   - unknown

8. Delivery requires an address.

9. Do not guess the customer's name.

10. Keep item-specific notes in item_note.

11. General notes should go into special_notes.

============================================================
CUSTOMER MESSAGE
============================================================

{message}

============================================================
OUTPUT
============================================================

Return only structured JSON matching the provided schema.
"""

    # ========================================================
    # GEMINI CLIENT
    # ========================================================

    client = genai.Client(
        api_key=api_key
    )

    # ========================================================
    # STRUCTURED JSON SCHEMA
    # ========================================================

    response_format = {
        "type": "text",
        "mime_type": "application/json",
        "schema": OrderAnalysis.model_json_schema(),
    }

    # ========================================================
    # GEMINI INTERACTIONS API
    # ========================================================

    response = client.interactions.create(
        model=model_name or MODEL_NAME,
        input=prompt,
        response_format=response_format,
    )

    # ========================================================
    # GET OUTPUT
    # ========================================================

    output_text = response.output_text

    if not output_text:
        raise ValueError(
            "Gemini tidak menghasilkan output."
        )

    # ========================================================
    # NORMAL JSON
    # ========================================================

    try:

        return OrderAnalysis.model_validate_json(
            output_text
        )

    except Exception:

        pass

    # ========================================================
    # JSON CODE FENCE FALLBACK
    # ========================================================

    cleaned = output_text.strip()

    if cleaned.startswith("```json"):

        cleaned = cleaned[
            len("```json"):
        ].strip()

    elif cleaned.startswith("```"):

        cleaned = cleaned[
            len("```"):
        ].strip()

    if cleaned.endswith("```"):

        cleaned = cleaned[
            :-len("```")
        ].strip()

    # ========================================================
    # JSON LOAD FALLBACK
    # ========================================================

    try:

        data = json.loads(
            cleaned
        )

        return OrderAnalysis.model_validate(
            data
        )

    except Exception as e:

        raise ValueError(
            "Output Gemini tidak dapat "
            f"divalidasi sebagai OrderAnalysis: {e}"
        )
