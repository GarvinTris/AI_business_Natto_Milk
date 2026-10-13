import csv
import os
import random
import urllib.parse
from datetime import date

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai_service import analyze_order

from business_rules import (
    calculate_capacity,
    calculate_order_workload,
    calculate_pricing,
    calculate_utilization,
    deterministic_missing_fields,
    order_status,
    operational_summary,
    validate_items,
)

# [BARU] modul monitoring (monitoring.py harus satu folder dengan app.py)
from monitoring import (
    ACTIVE_STAFF_STATUSES,
    now_iso,
    service_result,
    service_stats,
    recommend,
    alert_level,
    build_alert_message,
    should_send,
    manual_whatsapp_link,
    send_whatsapp_alert,
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

# [FIX] harus SETELAH load_dotenv() supaya isi .env terbaca
MANAGER_WHATSAPP = os.getenv("MANAGER_WHATSAPP", "")


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Smart Order Assistant Kedai Kopi UMKM",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# BUSINESS CONFIGURATION
# ============================================================

PRODUCT_CATALOG = {

    "Single Espresso": 22000,
    "Dual": 24000,
    "Americano": 24000,
    "Caffe Latte": 27000,
    "Cappuccino": 27000,
    "Caffe Mocha": 29000,
    "Caramel Macchiato": 29000,
    "Baileys Latte": 29000,
    "Rum Latte": 29000,
    "Hazelnut Latte": 29000,

    "Jombitto": 25000,
    "Jombitto Peach Tea": 27000,
    "Valerian's Latte": 28000,
    "Dark Chocolate": 25000,
    "Strawberry Cream Milk": 27000,

    "Matcha Latte": 24000,
    "Matcha Strawberry Latte": 28000,
    "Matcha Sea Salt Caramel Latte": 29000,

    "Long Black": 23000,
    "Salted Caramel Cold Brew": 27000,
    "Affogato": 28000,
    "Flat White": 27000,
    "Magic Latte": 28000,

    "Red Velvet": 25000,
    "Taro": 25000,

    "Almond Series - Original": 30000,
    "Almond Series - Chocolate": 32000,
    "Almond Series - Oreo": 32000,
    "Almond Series - Matcha": 32000,
    "Almond Series - Strawberry": 32000,
    "Almond Series - Banana": 33000,
    "Almond Series - Thai Tea": 28000,
    "Almond Series - Green Tea": 32000,
    "Almond Series - Honey": 28000,
    "Almond Series - Oat Choco Mint": 31000,

    "Oat Series - Original": 28000,
    "Oat Series - Chocolate": 30000,
    "Oat Series - Oreo": 30000,
    "Oat Series - Banana": 31000,
    "Oat Series - Strawberry": 30000,

    "Donat Goaded": 10000,
}


# ============================================================
# PRODUCT CATEGORIES
# ============================================================

PRODUCT_CATEGORIES = {

    "Regular Coffee": [
        "Single Espresso",
        "Dual",
        "Americano",
        "Caffe Latte",
        "Cappuccino",
        "Caffe Mocha",
        "Caramel Macchiato",
        "Baileys Latte",
        "Rum Latte",
        "Hazelnut Latte",
    ],

    "Positto Signature": [
        "Jombitto",
        "Jombitto Peach Tea",
        "Valerian's Latte",
        "Dark Chocolate",
        "Strawberry Cream Milk",
    ],

    "Matcha Series": [
        "Matcha Latte",
        "Matcha Strawberry Latte",
        "Matcha Sea Salt Caramel Latte",
    ],

    "Gourmet Signature": [
        "Long Black",
        "Salted Caramel Cold Brew",
        "Affogato",
        "Flat White",
        "Magic Latte",
    ],

    "Non Coffee": [
        "Red Velvet",
        "Taro",
    ],

    "Almond Series": [
        "Almond Series - Original",
        "Almond Series - Chocolate",
        "Almond Series - Oreo",
        "Almond Series - Matcha",
        "Almond Series - Strawberry",
        "Almond Series - Banana",
        "Almond Series - Thai Tea",
        "Almond Series - Green Tea",
        "Almond Series - Honey",
        "Almond Series - Oat Choco Mint",
    ],

    "Oat Series": [
        "Oat Series - Original",
        "Oat Series - Chocolate",
        "Oat Series - Oreo",
        "Oat Series - Banana",
        "Oat Series - Strawberry",
    ],

    "Snackies": [
        "Donat Goaded",
    ],
}


# ============================================================
# SAMPLE TYPES
# ============================================================

SAMPLE_TYPES = [
    "Dirty Data",
    "Semi Dirty Data",
    "Cleaned Data",
    "Natural Language Data",
]


# ============================================================
# SAMPLE TYPE CLASSIFICATION
# ============================================================

def classify_sample_type(
    message,
    expected_issue,
):

    message = (
        message or ""
    ).strip().lower()

    expected_issue = (
        expected_issue or ""
    ).strip().lower()

    # --------------------------------------------------------
    # CLEANED DATA
    # --------------------------------------------------------

    if expected_issue == "relatively complete":
        return "Cleaned Data"

    # --------------------------------------------------------
    # NATURAL LANGUAGE DATE
    # --------------------------------------------------------

    if expected_issue in {
        "natural language date",
    }:
        return "Natural Language Data"

    # --------------------------------------------------------
    # DIRTY DATA
    # --------------------------------------------------------

    if expected_issue in {
        "quantity date time fulfillment unclear",
        "missing exact address and time",
        "confirmation required before ordering",
        "missing menu and quantity",
        "unknown product",
    }:
        return "Dirty Data"

    # --------------------------------------------------------
    # SEMI DIRTY DATA
    # --------------------------------------------------------

    if expected_issue in {
        "unspecified delivery address details",
        "time ambiguous",
        "address not provided in this chat",
    }:
        return "Semi Dirty Data"

    # --------------------------------------------------------
    # NATURAL LANGUAGE KEYWORDS
    # --------------------------------------------------------

    natural_language_keywords = [

        "satu",
        "dua",
        "tiga",
        "empat",
        "lima",
        "enam",
        "tujuh",
        "delapan",
        "sembilan",
        "sepuluh",

        "besok",
        "lusa",
        "kemarin",
        "minggu depan",

        "jam lima",
        "jam empat",
        "jam tiga",
        "jam dua",
        "jam satu",
    ]

    if any(
        keyword in message
        for keyword in natural_language_keywords
    ):
        return "Natural Language Data"

    return "Semi Dirty Data"


# ============================================================
# LOAD SAMPLE CSV
# ============================================================

SAMPLE_MESSAGES = []


try:

    with open(
        "sample_message.csv",
        mode="r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            sample_id = (
                row.get(
                    "id",
                    "",
                ).strip()
            )

            message = (
                row.get(
                    "message",
                    "",
                ).strip()
            )

            expected_issue = (
                row.get(
                    "expected_issue",
                    "",
                ).strip()
            )

            if not message:
                continue

            sample_type = (
                row.get(
                    "sample_type",
                    "",
                ).strip()
            )

            if not sample_type:

                sample_type = (
                    classify_sample_type(
                        message,
                        expected_issue,
                    )
                )

            SAMPLE_MESSAGES.append(
                {
                    "id": sample_id,
                    "message": message,
                    "expected_issue": expected_issue,
                    "sample_type": sample_type,
                }
            )


except FileNotFoundError:

    st.warning(
        "File sample_message.csv tidak ditemukan."
    )


# ============================================================
# STAFF DATA
# ============================================================

STAFF_FILE = "staff.csv"


def load_staff_data():

    try:

        staff_df = pd.read_csv(
            STAFF_FILE
        )

    except FileNotFoundError:

        return pd.DataFrame(
            columns=[
                "employee_id",
                "name",
                "branch",
                "status",
            ]
        )

    required_columns = [
        "employee_id",
        "name",
        "branch",
        "status",
    ]

    for column in required_columns:

        if column not in staff_df.columns:

            staff_df[column] = ""

    staff_df["status"] = (
        staff_df["status"]
        .fillna("Unavailable")
        .astype(str)
        .str.strip()
    )

    return staff_df


# ============================================================
# SESSION STATE
# ============================================================

if "orders" not in st.session_state:
    st.session_state.orders = []


if "analysis" not in st.session_state:
    st.session_state.analysis = None


if "raw_message" not in st.session_state:
    st.session_state.raw_message = ""


if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False


if "whatsapp_message_preview" not in st.session_state:
    st.session_state.whatsapp_message_preview = ""


if "whatsapp_preview_source" not in st.session_state:
    st.session_state.whatsapp_preview_source = None


if "last_sample_by_type" not in st.session_state:
    st.session_state.last_sample_by_type = {}


if "staff_data" not in st.session_state:
    st.session_state.staff_data = load_staff_data()


# [BARU] state untuk alert manajer
if "last_alert_at" not in st.session_state:
    st.session_state.last_alert_at = None


if "last_alert_level" not in st.session_state:
    st.session_state.last_alert_level = None


# ============================================================
# OPERATIONAL CONFIGURATION
# ============================================================

# Assumption for prototype.
# This value should later be validated with the actual business.
CAPACITY_PER_STAFF = 5


# ============================================================
# WHATSAPP CONFIGURATION
# ============================================================

SELLER_WHATSAPP = "6285276133655"

DEFAULT_CUSTOMER_WHATSAPP = "6281350876454"


# ============================================================
# HEADER
# ============================================================

st.title(
    "🤖 AI Smart Order Assistant UMKM"
)

st.caption(
    "Customer Chat → Gemini AI → Structured Order → "
    "Business Rules → WhatsApp → Order Dashboard → "
    "Operational Monitoring"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Setup"
    )

    api_key = st.text_input(
        "Gemini API Key",
        value=os.getenv(
            "GEMINI_API_KEY",
            "",
        ),
        type="password",
        help=(
            "Disarankan simpan API Key "
            "di file .env."
        ),
    )

    model_name = st.text_input(
        "Model",
        value=os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash",
        ),
    )

    reference_date = st.date_input(
        "Reference date",
        value=date.today(),
    )

    st.caption(
        "Reference date digunakan AI untuk memahami "
        "'besok', 'lusa', 'Jumat', dan tanggal relatif lainnya."
    )

    st.divider()

    st.subheader(
        "📲 WhatsApp"
    )

    st.write(
        "Nomor UMKM / Seller"
    )

    st.code(
        SELLER_WHATSAPP
    )

    st.caption(
        "Pesan akan dibuka melalui WhatsApp Web "
        "dan perlu dikirim secara manual."
    )

    # [BARU] tampilkan nomor manajer penerima alert
    st.write(
        "Nomor Manajer (penerima alert)"
    )

    st.code(
        MANAGER_WHATSAPP or "belum diisi di .env"
    )


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "💬 Analyze Order",
        "📊 Order Dashboard",
        "🧠 AI vs Business Rules",
    ]
)


# ============================================================
# TAB 1 — ANALYZE ORDER
# ============================================================

with tab1:

    left, right = st.columns(
        [1, 1],
        gap="large",
    )

    # ========================================================
    # LEFT COLUMN
    # ========================================================

    with left:

        st.subheader(
            "1. Customer Chat"
        )

        if SAMPLE_MESSAGES:

            selected_type = st.selectbox(
                "Pilih tipe data",
                SAMPLE_TYPES,
            )

            matching_samples = [
                sample
                for sample in SAMPLE_MESSAGES
                if sample["sample_type"]
                == selected_type
            ]

            if matching_samples:

                if st.button(
                    "📋 Gunakan Contoh",
                    use_container_width=True,
                ):

                    last_sample_id = (
                        st.session_state
                        .last_sample_by_type
                        .get(
                            selected_type
                        )
                    )

                    available_samples = [
                        sample
                        for sample in matching_samples
                        if sample["id"]
                        != last_sample_id
                    ]

                    if not available_samples:

                        available_samples = (
                            matching_samples
                        )

                    selected_data = (
                        random.choice(
                            available_samples
                        )
                    )

                    st.session_state\
                        .last_sample_by_type[
                            selected_type
                        ] = (
                            selected_data["id"]
                        )

                    st.session_state.raw_message = (
                        selected_data["message"]
                    )

                    st.session_state.analysis = None

                    st.session_state.whatsapp_preview_source = (
                        None
                    )

                    st.rerun()

                st.caption(
                    f"Tersedia **{len(matching_samples)} sample** "
                    f"untuk tipe **{selected_type}**."
                )

            else:

                st.warning(
                    f"Belum ada sample untuk tipe "
                    f"**{selected_type}**."
                )

        else:

            st.warning(
                "sample_message.csv tidak ditemukan "
                "atau tidak memiliki data."
            )

        message = st.text_area(
            "Paste chat WhatsApp / Instagram customer",
            value=st.session_state.raw_message,
            height=220,
            placeholder=(
                "Contoh: Kak, besok mau 2 Caffe Latte, "
                "ambil sendiri jam 5..."
            ),
        )

        analyze_clicked = st.button(
            "✨ Analyze with Gemini AI",
            type="primary",
            use_container_width=True,
        )

        if analyze_clicked:

            if not message.strip():

                st.warning(
                    "Silakan masukkan chat customer "
                    "terlebih dahulu."
                )

            else:

                try:

                    with st.spinner(
                        "🤖 Gemini sedang memahami order..."
                    ):

                        st.session_state.analysis = (
                            analyze_order(
                                message=message,
                                api_key=api_key,
                                product_catalog=PRODUCT_CATALOG,
                                product_categories=PRODUCT_CATEGORIES,
                                model_name=model_name,
                                reference_date=(
                                    reference_date.isoformat()
                                ),
                            )
                        )

                        st.session_state.raw_message = (
                            message
                        )

                    st.success(
                        "✅ Analisis AI selesai."
                    )

                except Exception as e:

                    st.error(
                        f"Gagal menganalisis order: {e}"
                    )

    # ========================================================
    # RIGHT COLUMN
    # ========================================================

    with right:

        st.subheader(
            "2. AI Result"
        )

        analysis = (
            st.session_state.analysis
        )

        if analysis is None:

            st.info(
                "Masukkan chat customer kemudian klik "
                "**Analyze with Gemini AI**."
            )

        else:

            # =================================================
            # VALIDATE PRODUCTS
            # =================================================

            product_issues = validate_items(
                analysis,
                PRODUCT_CATALOG,
                PRODUCT_CATEGORIES,
            )

            # =================================================
            # PRICING
            # =================================================

            price_rows, grand_total = (
                calculate_pricing(
                    analysis,
                    PRODUCT_CATALOG,
                )
            )

            # =================================================
            # STATUS
            # =================================================

            missing = (
                deterministic_missing_fields(
                    analysis
                )
            )

            all_issues = list(
                dict.fromkeys(
                    product_issues
                    + missing
                )
            )

            if product_issues:

                status = "NEEDS CONFIRMATION"

            else:

                status = order_status(
                    analysis,
                    grand_total,
                )

            if status == "READY":

                st.success(
                    "✅ ORDER READY"
                )

            else:

                st.warning(
                    "⚠️ NEEDS CONFIRMATION"
                )

            # =================================================
            # METRICS
            # =================================================

            c1, c2, c3 = st.columns(3)

            total_items = sum(
                item.quantity
                for item in analysis.items
            )

            c1.metric(
                "Total Items",
                total_items,
            )

            c2.metric(
                "Fulfillment",
                analysis.fulfillment.upper(),
            )

            c3.metric(
                "Status",
                status,
            )

            # =================================================
            # STRUCTURED INFORMATION
            # =================================================

            st.markdown(
                "### 📋 Structured Information"
            )

            info_df = pd.DataFrame(
                [
                    [
                        "Customer",
                        analysis.customer_name or "-",
                    ],

                    [
                        "Date",
                        analysis.order_date or "-",
                    ],

                    [
                        "Time",
                        analysis.order_time or "-",
                    ],

                    [
                        "Fulfillment",
                        analysis.fulfillment.upper(),
                    ],

                    [
                        "Address",
                        analysis.address or "-",
                    ],
                ],
                columns=[
                    "Field",
                    "Value",
                ],
            )

            st.dataframe(
                info_df,
                use_container_width=True,
                hide_index=True,
            )

            # =================================================
            # ITEMS & PRICING
            # =================================================

            st.markdown(
                "### 💰 Items & Pricing"
            )

            if price_rows:

                price_df = pd.DataFrame(
                    price_rows
                )

                for col in [
                    "Unit Price",
                    "Subtotal",
                ]:

                    price_df[col] = (
                        price_df[col].apply(
                            lambda x:
                            "-"
                            if pd.isna(x)
                            else
                            f"Rp{x:,.0f}".replace(
                                ",",
                                ".",
                            )
                        )
                    )

                st.dataframe(
                    price_df,
                    use_container_width=True,
                    hide_index=True,
                )

                st.markdown(
                    f"### Total: "
                    f"Rp{grand_total:,.0f}"
                    .replace(
                        ",",
                        ".",
                    )
                )

            # =================================================
            # VALIDATION
            # =================================================

            if all_issues:

                st.markdown(
                    "### ⚠️ Information / Validation"
                )

                for issue in all_issues:

                    st.warning(
                        issue
                    )

            # =================================================
            # WHATSAPP
            # =================================================

            st.divider()

            st.subheader(
                "📲 WhatsApp"
            )

            customer_whatsapp = st.text_input(
                "Nomor WhatsApp Customer",
                value=DEFAULT_CUSTOMER_WHATSAPP,
                key="customer_whatsapp",
            )

            clean_phone = (
                customer_whatsapp
                .replace("+", "")
                .replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )

            if clean_phone.startswith("08"):

                clean_phone = (
                    "62"
                    + clean_phone[1:]
                )

            # =================================================
            # PRODUCT TEXT
            # =================================================

            product_lines = []

            for item in analysis.items:

                product_line = (
                    f"- {item.product_name or '-'} "
                    f"x{item.quantity}"
                )

                if item.size_or_variant:

                    product_line += (
                        f" ({item.size_or_variant})"
                    )

                if item.item_note:

                    product_line += (
                        f"\n  📝 {item.item_note}"
                    )

                product_lines.append(
                    product_line
                )

            product_text = "\n".join(
                product_lines
            )

            # =================================================
            # WHATSAPP MESSAGE
            # =================================================

            customer_name = (
                analysis.customer_name
                if analysis.customer_name
                else ""
            )

            formatted_total = (
                f"Rp{grand_total:,.0f}"
                .replace(
                    ",",
                    ".",
                )
            )

            if status == "READY":

                whatsapp_message = (
                    f"Halo Kak"
                    f"{' ' + customer_name if customer_name else ''}"
                    f" 😊\n\n"

                    "Pesanan Kakak sudah kami catat:\n\n"

                    f"{product_text}\n\n"

                    f"📅 Tanggal: "
                    f"{analysis.order_date or '-'}\n"

                    f"🕒 Jam: "
                    f"{analysis.order_time or '-'}\n"

                    f"🚚 Metode: "
                    f"{analysis.fulfillment.upper()}\n"
                )

                if analysis.fulfillment == "delivery":

                    whatsapp_message += (
                        f"📍 Alamat: "
                        f"{analysis.address or '-'}\n"
                    )

                whatsapp_message += (
                    f"\n💰 Total Pesanan: "
                    f"{formatted_total}\n\n"

                    "Apakah detail pesanan sudah benar, Kak?\n\n"

                    "Terima kasih."
                )

            else:

                field_labels = {

                    "tanggal":
                        "tanggal pesanan",

                    "jam":
                        "jam pengambilan/pengantaran",

                    "metode pesanan":
                        "metode penerimaan "
                        "(dine-in, takeaway, atau delivery)",

                    "alamat delivery":
                        "alamat lengkap pengantaran",

                    "menu/jumlah pesanan":
                        "menu dan jumlah yang ingin dipesan",
                }

                confirmation_fields = list(
                    dict.fromkeys(
                        field_labels.get(
                            field.lower().strip(),
                            field.replace(
                                "_",
                                " ",
                            )
                        )
                        for field
                        in all_issues
                    )
                )

                confirmation_text = "\n".join(
                    f"{number}. {field}"
                    for number, field
                    in enumerate(
                        confirmation_fields,
                        start=1,
                    )
                )

                whatsapp_message = (
                    f"Halo Kak"
                    f"{' ' + customer_name if customer_name else ''}"
                    f" 😊\n\n"

                    "Terima kasih atas pesanannya.\n\n"

                    "Mohon lengkapi atau konfirmasi "
                    "informasi berikut ya, Kak:\n"

                    f"{confirmation_text}\n\n"

                    "Silakan balas melalui chat ini. "
                    "Terima kasih."
                )

            # =================================================
            # MESSAGE PREVIEW
            # =================================================

            st.markdown(
                "#### ✨ Preview Pesan"
            )

            preview_source = (
                st.session_state.raw_message,
                analysis.model_dump_json(),
                whatsapp_message,
            )

            if (
                st.session_state.get(
                    "whatsapp_preview_source"
                )
                != preview_source
            ):

                st.session_state.whatsapp_message_preview = (
                    whatsapp_message
                )

                st.session_state.whatsapp_preview_source = (
                    preview_source
                )

            whatsapp_message = st.text_area(
                "Pesan WhatsApp",
                height=250,
                key="whatsapp_message_preview",
            )

            # =================================================
            # CREATE WHATSAPP URL
            # =================================================

            if (
                clean_phone
                and whatsapp_message.strip()
            ):

                encoded_message = (
                    urllib.parse.quote(
                        whatsapp_message
                    )
                )

                whatsapp_url = (
                    f"https://wa.me/{clean_phone}"
                    f"?text={encoded_message}"
                )

                st.success(
                    f"📱 Customer: {clean_phone}"
                )

                st.link_button(
                    "📲 Kirim ke WhatsApp Customer",
                    whatsapp_url,
                    use_container_width=True,
                    type="primary",
                )

                st.info(
                    "WhatsApp Web akan terbuka dengan "
                    "pesan yang sudah disiapkan. "
                    "Tekan Send untuk mengirim."
                )

            # =================================================
            # SAVE ORDER
            # =================================================

            st.divider()

            if st.button(
                "💾 Save to Order Dashboard",
                use_container_width=True,
            ):

                product_text_dashboard = (
                    "; ".join(
                        f"{x.product_name} "
                        f"x{x.quantity}"
                        for x
                        in analysis.items
                    )
                )

                st.session_state.orders.append(
                    {

                        "Customer Chat":
                            st.session_state.raw_message,

                        "Customer":
                            analysis.customer_name
                            or "-",

                        "WhatsApp":
                            clean_phone,

                        "Products":
                            product_text_dashboard
                            or "-",

                        "Items":
                            [
                                item.model_dump()
                                for item
                                in analysis.items
                            ],

                        "Date":
                            analysis.order_date
                            or "-",

                        "Time":
                            analysis.order_time
                            or "-",

                        "Fulfillment":
                            analysis.fulfillment,

                        "Address":
                            analysis.address
                            or "-",

                        "Total":
                            grand_total,

                        "Status":
                            status,

                        "Operational Status":
                            "Active",

                        # [BARU] pencatatan waktu layanan
                        "Created At":
                            now_iso(),

                        "Finished At":
                            None,

                        "Bartender":
                            "-",
                    }
                )

                st.success(
                    "✅ Order berhasil disimpan "
                    "ke dashboard."
                )


# ============================================================
# TAB 2 — ORDER & OPERATION DASHBOARD
# ============================================================

with tab2:

    st.subheader(
        "📊 Order & Operational Dashboard"
    )

    # ========================================================
    # STAFF DATA
    # ========================================================

    staff_df = (
        st.session_state.staff_data.copy()
    )

    if staff_df.empty:

        st.warning(
            "staff.csv tidak ditemukan atau kosong."
        )

    else:

        # ====================================================
        # OPERATIONAL STAFF OVERVIEW
        # ====================================================

        st.markdown(
            "### 👥 Staff Availability"
        )

        total_staff = len(
            staff_df
        )

        # [FIX] sebelumnya == "Available", padahal staff.csv
        # berisi "Working" sehingga staff aktif selalu 0
        active_staff = int(
            (
                staff_df["status"]
                .isin(ACTIVE_STAFF_STATUSES)
            ).sum()
        )

        unavailable_staff = (
            total_staff
            - active_staff
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Active Staff",
            f"{active_staff} / {total_staff}",
        )

        c2.metric(
            "Unavailable",
            unavailable_staff,
        )

        c3.metric(
            "Capacity / Staff",
            CAPACITY_PER_STAFF,
        )

        # ====================================================
        # STAFF TABLE
        # ====================================================

        display_staff = staff_df.copy()

        display_staff = (
            display_staff[
                [
                    "employee_id",
                    "name",
                    "branch",
                    "status",
                ]
            ]
            .rename(
                columns={
                    "employee_id":
                        "Employee ID",

                    "name":
                        "Name",

                    "branch":
                        "Branch",

                    "status":
                        "Availability",
                }
            )
        )

        st.dataframe(
            display_staff,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Staff availability dibaca dari staff.csv. "
            "Dashboard tidak mengubah attendance atau "
            "status staff secara manual."
        )

        # ====================================================
        # WORKLOAD
        # ====================================================

        workload = (
            calculate_order_workload(
                st.session_state.orders,
                None,
            )
        )

        # ====================================================
        # CAPACITY
        # ====================================================

        capacity = (
            calculate_capacity(
                active_staff,
                CAPACITY_PER_STAFF,
            )
        )

        # ====================================================
        # UTILIZATION
        # ====================================================

        utilization = (
            calculate_utilization(
                workload,
                capacity,
            )
        )

        # ====================================================
        # OPERATION SUMMARY
        # ====================================================

        summary = operational_summary(
            active_staff_count=active_staff,
            total_staff_count=total_staff,
            workload=workload,
            capacity=capacity,
        )

        st.divider()

        st.markdown(
            "### ⚙️ Operational Capacity"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Current Workload",
            workload,
        )

        c2.metric(
            "Current Capacity",
            capacity,
        )

        c3.metric(
            "Utilization",
            f"{utilization:.0f}%",
        )

        # ====================================================
        # OPERATIONAL INTERPRETATION
        # ====================================================

        if capacity == 0:

            st.error(
                "Tidak ada staff yang tersedia. "
                "Workload belum memiliki kapasitas staff "
                "untuk ditangani."
            )

        elif utilization < 80:

            st.success(
                "Kondisi operasional masih berada "
                "di bawah kapasitas yang tersedia."
            )

        elif utilization < 100:

            st.warning(
                "Workload mulai mendekati kapasitas "
                "staff yang tersedia."
            )

        else:

            st.error(
                "Workload saat ini melebihi kapasitas "
                "staff yang tersedia."
            )

        st.caption(
            "Capacity per staff saat ini adalah "
            f"{CAPACITY_PER_STAFF} workload units "
            "sebagai asumsi prototype. "
            "Angka ini perlu divalidasi dengan kondisi "
            "operasional usaha."
        )

        # ====================================================
        # [BARU] SERVICE MONITORING
        # (menggantikan st.info(summary) yang menampilkan
        #  dictionary mentah)
        # ====================================================

        stats = service_stats(
            st.session_state.orders
        )

        st.markdown(
            "### 📝 Service Monitoring"
        )

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "Tepat waktu",
            stats["on_time"],
        )

        m2.metric(
            "Berhasil tapi lambat",
            stats["slow"],
        )

        m3.metric(
            "Sedang diproses",
            stats["in_progress"],
        )

        m4.metric(
            "Rata-rata (menit)",
            f"{stats['avg_minutes']:.1f}",
        )

        if stats["by_bartender"]:

            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Bartender": name,
                            "Selesai": data["done"],
                            "Lambat": data["slow"],
                        }
                        for name, data
                        in stats["by_bartender"].items()
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

        # ====================================================
        # [BARU] REKOMENDASI UNTUK MANAJER
        # ====================================================

        st.markdown(
            "### 💡 Rekomendasi untuk Manajer"
        )

        recs = recommend(
            utilization,
            active_staff,
            total_staff,
            stats,
        )

        show_by_level = {
            "critical": st.error,
            "warning": st.warning,
            "info": st.info,
            "ok": st.success,
        }

        for level_name, rec_text in recs:

            show_by_level[level_name](
                rec_text
            )

        # ====================================================
        # [BARU] ALERT KE MANAJER (WHATSAPP)
        # ====================================================

        current_level = alert_level(recs)

        if current_level:

            alert_summary = {
                "active_staff": active_staff,
                "total_staff": total_staff,
                "workload": workload,
                "capacity": capacity,
                "utilization": utilization,
            }

            alert_message = build_alert_message(
                current_level,
                alert_summary,
                stats,
                recs,
            )

            st.markdown(
                "### 📲 Alert ke Manajer"
            )

            st.text(
                alert_message
            )

            auto_send = st.toggle(
                "Kirim otomatis ke WhatsApp manajer",
                value=False,
                key="auto_send_alert",
            )

            if not MANAGER_WHATSAPP:

                st.warning(
                    "Isi MANAGER_WHATSAPP di file .env "
                    "(format 62812xxxxxxx)."
                )

            else:

                manual_link = manual_whatsapp_link(
                    MANAGER_WHATSAPP,
                    alert_message,
                )

                if auto_send and should_send(
                    st.session_state.last_alert_at,
                    st.session_state.last_alert_level,
                    current_level,
                ):

                    sent_ok, sent_info = (
                        send_whatsapp_alert(
                            MANAGER_WHATSAPP,
                            alert_message,
                        )
                    )

                    if sent_ok:

                        st.session_state.last_alert_at = (
                            now_iso()
                        )

                        st.session_state.last_alert_level = (
                            current_level
                        )

                        st.success(
                            "Alert terkirim ke manajer."
                        )

                    elif sent_info.startswith(
                        "https://wa.me"
                    ):

                        # FONNTE_TOKEN kosong -> kirim manual
                        st.link_button(
                            "📲 Kirim manual lewat WhatsApp",
                            sent_info,
                        )

                    else:

                        st.error(
                            sent_info
                        )

                else:

                    st.link_button(
                        "📲 Kirim manual lewat WhatsApp",
                        manual_link,
                    )

    # ========================================================
    # ORDER DASHBOARD
    # ========================================================

    st.divider()

    st.markdown(
        "### 🧾 Order Dashboard"
    )

    if not st.session_state.orders:

        st.info(
            "Belum ada order tersimpan."
        )

    else:

        orders_df = pd.DataFrame(
            st.session_state.orders
        )

        # ====================================================
        # ORDER METRICS
        # ====================================================

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Orders",
            len(orders_df),
        )

        c2.metric(
            "Ready Orders",
            int(
                (
                    orders_df["Status"]
                    == "READY"
                ).sum()
            ),
        )

        total_revenue = (
            orders_df["Total"].sum()
        )

        c3.metric(
            "Potential Revenue",
            f"Rp{total_revenue:,.0f}"
            .replace(
                ",",
                ".",
            ),
        )

        # ====================================================
        # [BARU] PROSES ORDER (pilih bartender + tombol selesai)
        # Harus berada DI ATAS selectbox "Order Status" agar
        # session_state key-nya bisa diubah dengan aman.
        # ====================================================

        st.markdown(
            "#### ⏱️ Proses Order"
        )

        bartender_names = (
            staff_df["name"].astype(str).tolist()
            if not staff_df.empty
            else []
        )

        active_found = False

        for order_index, order_data in enumerate(
            st.session_state.orders
        ):

            if (
                order_data.get(
                    "Operational Status",
                    "Active",
                )
                != "Active"
            ):
                continue

            active_found = True

            col_a, col_b = st.columns([3, 1])

            chosen_bartender = col_a.selectbox(
                (
                    f"Order #{order_index + 1} — "
                    f"{order_data.get('Products', '-')}"
                ),
                ["-"] + bartender_names,
                key=f"bartender_{order_index}",
            )

            if col_b.button(
                "✅ Selesai",
                key=f"finish_{order_index}",
            ):

                order_data["Bartender"] = (
                    chosen_bartender
                )

                order_data["Finished At"] = (
                    now_iso()
                )

                order_data["Operational Status"] = (
                    "Completed"
                )

                # sinkronkan dengan selectbox Order Status
                # di bawah agar tidak kembali ke "Active"
                st.session_state[
                    f"order_operational_status_{order_index}"
                ] = "Completed"

                st.rerun()

        if not active_found:

            st.caption(
                "Tidak ada order yang sedang diproses."
            )

        # ====================================================
        # OPERATIONAL STATUS
        # ====================================================

        if "Operational Status" not in orders_df.columns:

            orders_df[
                "Operational Status"
            ] = "Active"

        st.markdown(
            "#### Order Status"
        )

        for index, order in orders_df.iterrows():

            current_operational_status = (
                order.get(
                    "Operational Status",
                    "Active",
                )
            )

            operational_options = [
                "Active",
                "Completed",
                "Cancelled",
            ]

            if (
                current_operational_status
                not in operational_options
            ):

                current_operational_status = (
                    "Active"
                )

            new_status = st.selectbox(
                (
                    f"Order #{index + 1} — "
                    f"{order.get('Products', '-')}"
                ),
                operational_options,
                index=operational_options.index(
                    current_operational_status
                ),
                key=f"order_operational_status_{index}",
            )

            if (
                new_status
                != st.session_state.orders[
                    index
                ].get(
                    "Operational Status",
                    "Active",
                )
            ):

                st.session_state.orders[
                    index
                ]["Operational Status"] = (
                    new_status
                )

                # [BARU] bila diselesaikan lewat dropdown ini,
                # catat juga waktu selesainya
                if (
                    new_status == "Completed"
                    and not st.session_state.orders[
                        index
                    ].get("Finished At")
                ):

                    st.session_state.orders[
                        index
                    ]["Finished At"] = now_iso()

        # ====================================================
        # REFRESH DATAFRAME
        # ====================================================

        orders_df = pd.DataFrame(
            st.session_state.orders
        )

        # ====================================================
        # DISPLAY TABLE
        # ====================================================

        display_df = orders_df.copy()

        if "Items" in display_df.columns:

            display_df = display_df.drop(
                columns=[
                    "Items"
                ]
            )

        # [BARU] kolom hasil layanan per order
        display_df["Hasil Layanan"] = [
            service_result(o)
            for o in st.session_state.orders
        ]

        if "Total" in display_df.columns:

            display_df["Total"] = (
                display_df["Total"].apply(
                    lambda x:
                    f"Rp{x:,.0f}"
                    .replace(
                        ",",
                        ".",
                    )
                )
            )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

        # ====================================================
        # DOWNLOAD CSV
        # ====================================================

        csv_data = (
            orders_df
            .drop(
                columns=[
                    "Items"
                ],
                errors="ignore",
            )
            .to_csv(
                index=False
            )
            .encode(
                "utf-8"
            )
        )

        st.download_button(
            "⬇️ Download orders.csv",
            data=csv_data,
            file_name="orders.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ============================================================
# TAB 3 — AI VS BUSINESS RULES
# ============================================================

with tab3:

    st.subheader(
        "🧠 Mana AI, Mana Business Rule?"
    )

    st.markdown(
        """
| Task | AI | Normal Code / Rules |
|---|:---:|:---:|
| Memahami bahasa customer | ✅ | |
| Mengenali nama produk | ✅ | |
| Memahami “besok/lusa/Jumat” | ✅ | |
| Mengenali alamat | ✅ | |
| Menemukan informasi ambigu | ✅ | |
| Menentukan menu dan jumlah dari bahasa natural | ✅ | |
| Menentukan harga | | ✅ |
| Menghitung subtotal | | ✅ |
| Menghitung total | | ✅ |
| Menentukan field yang wajib dilengkapi | | ✅ |
| Delivery wajib alamat | | ✅ |
| Menentukan READY | | ✅ |
| Menentukan NEEDS CONFIRMATION | | ✅ |
| Mengukur workload | | ✅ |
| Menghitung capacity | | ✅ |
| Menghitung utilization | | ✅ |
| Membaca staff availability | | ✅ |
| Status layanan (tepat waktu / lambat) | | ✅ |
| Rekomendasi SDM untuk manajer | | ✅ |
| Alert WhatsApp ke manajer | | ✅ |
"""
    )

    st.markdown(
        "### 🔄 AI Business Process"
    )

    st.code(
        """
Customer WhatsApp
        ↓
Unstructured Chat
        ↓
Gemini AI
        ↓
Structured Order
        ↓
Business Rules
        ↓
Check Required Information
        ↓
Calculate Price
        ↓
Order Dashboard
        ↓
Staff Availability
        ↓
Active Staff
        ↓
Workload
        ↓
Capacity
        ↓
Utilization
        ↓
Service Monitoring
        ↓
Recommendation + WhatsApp Alert to Manager
        """
    )

    st.markdown(
        "### 🏪 Operational Monitoring"
    )

    st.code(
        """
STAFF DATA
    ↓
Available / Working
    ↓
Active Staff
    ↓
        ┌──────────────────┐
        │                  │
        ▼                  ▼
   ORDER DATA        CAPACITY/STAFF
        │                  │
        ▼                  ▼
     WORKLOAD          CAPACITY
        │                  │
        └────────┬─────────┘
                 ↓
            UTILIZATION
                 ↓
   Service result (tepat waktu / lambat)
                 ↓
   Recommendation → WhatsApp alert
        """
    )

    st.markdown(
        "### 🛒 Katalog Produk"
    )

    catalog_df = pd.DataFrame(
        [
            {
                "Category": category,
                "Product": product,
                "Price": PRODUCT_CATALOG[
                    product
                ],
            }

            for category, products
            in PRODUCT_CATEGORIES.items()

            for product
            in products
        ]
    )

    catalog_df["Price"] = (
        catalog_df["Price"].apply(
            lambda x:
            f"Rp{x:,.0f}".replace(
                ",",
                ".",
            )
        )
    )

    st.dataframe(
        catalog_df,
        use_container_width=True,
        hide_index=True,
    )
