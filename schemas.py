from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================
# ORDER ITEM
# ============================================================

class OrderItem(BaseModel):

    product_name: Optional[str] = None

    product_category: Optional[str] = None

    quantity: int = Field(
        default=1,
        ge=1
    )

    size_or_variant: Optional[str] = None

    item_note: Optional[str] = None


# ============================================================
# ORDER ANALYSIS
# ============================================================

class OrderAnalysis(BaseModel):

    customer_name: Optional[str] = None

    items: List[OrderItem] = Field(
        default_factory=list
    )

    order_date: Optional[str] = None

    order_time: Optional[str] = None

    fulfillment: Literal[
        "dine_in",
        "takeaway",
        "delivery",
        "unknown"
    ] = "unknown"

    address: Optional[str] = None

    special_notes: Optional[str] = None

    missing_fields: List[str] = Field(
        default_factory=list
    )

    order_summary: Optional[str] = None

    follow_up_message: Optional[str] = None
