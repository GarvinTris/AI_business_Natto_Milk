# ============================================================
# CATEGORY RULES
# ============================================================

CATEGORY_RULES = {

    "Regular Coffee": {
        "variant_required": True,
        "allowed_variants": [
            "Hot",
            "Cold",
            "Ice",
        ],
    },

    "Gourmet Signature": {
        "variant_required": False,
        "allowed_variants": [
            "Cold",
        ],
    },

    "Positto Signature": {
        "variant_required": False,
        "allowed_variants": [],
    },

    "Matcha Series": {
        "variant_required": False,
        "allowed_variants": [],
    },

    "Non Coffee": {
        "variant_required": False,
        "allowed_variants": [],
    },

    "Almond Series": {
        "variant_required": False,
        "allowed_variants": [],
    },

    "Oat Series": {
        "variant_required": False,
        "allowed_variants": [],
    },

    "Snackies": {
        "variant_required": False,
        "allowed_variants": [],
    },
}


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value):

    if value is None:
        return ""

    return str(value).strip()


def find_product_category(
    product_name,
    product_categories,
):

    product_name = normalize_text(
        product_name
    )

    for category, products in product_categories.items():

        if product_name in products:
            return category

    return None


# ============================================================
# VALIDATE PRODUCTS
# ============================================================

def validate_items(
    analysis,
    product_catalog,
    product_categories,
):

    issues = []

    for index, item in enumerate(
        analysis.items,
        start=1
    ):

        product_name = normalize_text(
            item.product_name
        )

        if not product_name:

            issues.append(
                f"Item {index}: menu belum ditentukan."
            )

            continue

        # ----------------------------------------------------
        # PRODUCT EXISTS
        # ----------------------------------------------------

        if product_name not in product_catalog:

            issues.append(
                f"Item {index}: "
                f"produk '{product_name}' "
                "tidak ditemukan di katalog."
            )

            continue

        # ----------------------------------------------------
        # FIND CATEGORY
        # ----------------------------------------------------

        actual_category = find_product_category(
            product_name,
            product_categories,
        )

        if actual_category is None:

            issues.append(
                f"Item {index}: kategori produk "
                f"'{product_name}' tidak ditemukan."
            )

            continue

        # ----------------------------------------------------
        # CATEGORY CONSISTENCY
        # ----------------------------------------------------

        if (
            item.product_category
            and item.product_category
            != actual_category
        ):

            issues.append(
                f"Item {index}: kategori produk "
                f"'{product_name}' tidak sesuai katalog."
            )

        # ----------------------------------------------------
        # VARIANT RULE
        # ----------------------------------------------------

        category_rule = CATEGORY_RULES.get(
            actual_category,
            {}
        )

        variant_required = category_rule.get(
            "variant_required",
            False
        )

        allowed_variants = category_rule.get(
            "allowed_variants",
            []
        )

        variant = normalize_text(
            item.size_or_variant
        )

        if variant_required and not variant:

            issues.append(
                f"Item {index}: variant untuk "
                f"'{product_name}' wajib diisi."
            )

        if (
            variant
            and allowed_variants
            and variant.lower()
            not in [
                x.lower()
                for x in allowed_variants
            ]
        ):

            issues.append(
                f"Item {index}: variant "
                f"'{variant}' tidak valid untuk "
                f"'{product_name}'."
            )

    return issues


# ============================================================
# PRICING
# ============================================================

def calculate_pricing(
    analysis,
    product_catalog,
):

    price_rows = []

    grand_total = 0

    for item in analysis.items:

        product_name = normalize_text(
            item.product_name
        )

        quantity = item.quantity

        if (
            not product_name
            or product_name
            not in product_catalog
        ):

            price_rows.append(
                {
                    "Product": product_name or "-",
                    "Quantity": quantity,
                    "Unit Price": None,
                    "Subtotal": None,
                }
            )

            continue

        unit_price = product_catalog[
            product_name
        ]

        subtotal = (
            unit_price
            * quantity
        )

        grand_total += subtotal

        price_rows.append(
            {
                "Product": product_name,
                "Quantity": quantity,
                "Unit Price": unit_price,
                "Subtotal": subtotal,
            }
        )

    return price_rows, grand_total


# ============================================================
# DETERMINISTIC MISSING FIELDS
# ============================================================

def deterministic_missing_fields(
    analysis,
):

    missing = []

    # --------------------------------------------------------
    # MENU
    # --------------------------------------------------------

    if not analysis.items:

        missing.append(
            "menu/jumlah pesanan"
        )

    else:

        for item in analysis.items:

            if not item.product_name:

                missing.append(
                    "menu/jumlah pesanan"
                )

                break

            if item.quantity < 1:

                missing.append(
                    "menu/jumlah pesanan"
                )

                break

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if not analysis.order_date:

        missing.append(
            "tanggal"
        )

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    if not analysis.order_time:

        missing.append(
            "jam"
        )

    # --------------------------------------------------------
    # FULFILLMENT
    # --------------------------------------------------------

    if (
        analysis.fulfillment == "unknown"
        or not analysis.fulfillment
    ):

        missing.append(
            "metode pesanan"
        )

    # --------------------------------------------------------
    # DELIVERY ADDRESS
    # --------------------------------------------------------

    if (
        analysis.fulfillment == "delivery"
        and not analysis.address
    ):

        missing.append(
            "alamat delivery"
        )

    return list(
        dict.fromkeys(
            missing
        )
    )


# ============================================================
# ORDER STATUS
# ============================================================

def order_status(
    analysis,
    grand_total=None,
):

    missing = deterministic_missing_fields(
        analysis
    )

    if missing:

        return "NEEDS CONFIRMATION"

    return "READY"


# ============================================================
# OPERATIONAL WORKLOAD
# ============================================================

def calculate_order_workload(
    orders,
    branch,
):

    workload = 0

    for order in orders:

        if order.get("Branch") != branch:
            continue

        operational_status = (
            order.get(
                "Operational Status",
                "Active"
            )
        )

        if operational_status in {
            "Completed",
            "Cancelled",
        }:

            continue

        items = order.get(
            "Items",
            []
        )

        for item in items:

            try:

                quantity = int(
                    item.get(
                        "quantity",
                        0
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                quantity = 0

            workload += quantity

    return workload


# ============================================================
# CAPACITY
# ============================================================

def calculate_capacity(
    active_staff_count,
    capacity_per_staff,
):

    if active_staff_count <= 0:

        return 0

    return (
        active_staff_count
        * capacity_per_staff
    )


# ============================================================
# UTILIZATION
# ============================================================

def calculate_utilization(
    workload,
    capacity,
):

    if capacity <= 0:

        return 0

    return (
        workload
        / capacity
    ) * 100


# ============================================================
# OPERATIONAL SUMMARY
# ============================================================

def operational_summary(
    active_staff_count,
    total_staff_count,
    workload,
    capacity,
):

    utilization = calculate_utilization(
        workload,
        capacity,
    )

    return {
        "active_staff": active_staff_count,
        "total_staff": total_staff_count,
        "workload": workload,
        "capacity": capacity,
        "utilization": utilization,
    }
