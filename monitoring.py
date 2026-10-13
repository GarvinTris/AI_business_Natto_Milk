"""
monitoring.py — tambahan untuk AI Smart Order (Natto Milk)
Isi: status layanan per order, statistik, rekomendasi SDM, alert WhatsApp ke manajer.
Semua deterministik (tanpa LLM), sesuai prinsip "angka = business rules".
"""
import os
import urllib.parse
from datetime import datetime

# ------------------------------------------------------------
# KONFIGURASI (ASUMSI PROTOTYPE — validasi dengan kondisi kedai)
# ------------------------------------------------------------
# <- memperbaiki bug "Working"
ACTIVE_STAFF_STATUSES = {"Available", "Working"}
TARGET_MINUTES = 10          # order dianggap lambat bila > 10 menit sejak masuk
UTIL_WARNING = 80            # % utilisasi peringatan dini
UTIL_CRITICAL = 100          # % utilisasi kritis
SLOW_RATIO_LIMIT = 0.30      # >30% order selesai lambat = masalah
MIN_FINISHED_FOR_STATS = 3   # minimal order selesai agar rekomendasi dipercaya
ALERT_COOLDOWN_MIN = 15      # jangan kirim alert yang sama lebih sering dari ini


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _minutes(start_iso, end_iso):
    try:
        delta = datetime.fromisoformat(
            end_iso) - datetime.fromisoformat(start_iso)
        return delta.total_seconds() / 60
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------
# STATUS LAYANAN PER ORDER
# ------------------------------------------------------------
def service_result(order):
    """Return: Dibatalkan | Dalam proses | Berhasil tepat waktu | Berhasil tapi lambat"""
    if order.get("Operational Status") == "Cancelled":
        return "Dibatalkan"
    minutes = _minutes(order.get("Created At"), order.get("Finished At"))
    if minutes is None:
        return "Dalam proses"
    return "Berhasil tepat waktu" if minutes <= TARGET_MINUTES else "Berhasil tapi lambat"


def service_stats(orders):
    stats = {"on_time": 0, "slow": 0, "in_progress": 0, "cancelled": 0,
             "avg_minutes": 0.0, "slow_ratio": 0.0, "finished": 0,
             "by_bartender": {}}
    durations = []
    for o in orders:
        r = service_result(o)
        if r == "Berhasil tepat waktu":
            stats["on_time"] += 1
        elif r == "Berhasil tapi lambat":
            stats["slow"] += 1
        elif r == "Dibatalkan":
            stats["cancelled"] += 1
        else:
            stats["in_progress"] += 1
        if r.startswith("Berhasil"):
            m = _minutes(o.get("Created At"), o.get("Finished At"))
            durations.append(m)
            b = o.get("Bartender") or "-"
            d = stats["by_bartender"].setdefault(b, {"done": 0, "slow": 0})
            d["done"] += 1
            d["slow"] += r == "Berhasil tapi lambat"
    stats["finished"] = stats["on_time"] + stats["slow"]
    if durations:
        stats["avg_minutes"] = sum(durations) / len(durations)
        stats["slow_ratio"] = stats["slow"] / stats["finished"]
    return stats


# ------------------------------------------------------------
# REKOMENDASI UNTUK MANAJER
# ------------------------------------------------------------
def recommend(utilization, active_staff, total_staff, stats):
    """Return list of (level, text). level: critical | warning | info | ok"""
    recs = []
    absent = total_staff - active_staff
    reliable = stats["finished"] >= MIN_FINISHED_FOR_STATS
    slow_bad = reliable and stats["slow_ratio"] > SLOW_RATIO_LIMIT

    if active_staff == 0:
        recs.append(
            ("critical", "Tidak ada staff aktif. Hubungi staff cadangan sekarang."))
        return recs

    if utilization >= UTIL_CRITICAL:
        if absent > 0:
            recs.append(("critical",
                         f"Beban {utilization:.0f}% dan {absent} staff tidak hadir. "
                         "Panggil staff yang off atau cari pengganti hari ini."))
        elif slow_bad:
            recs.append(("critical",
                         f"Beban {utilization:.0f}% dan {stats['slow_ratio']:.0%} order selesai lambat "
                         "meski semua staff hadir. Tambah 1 staff part-time; "
                         "bila terjadi berulang, pertimbangkan merekrut karyawan tetap."))
        else:
            recs.append(("critical",
                         f"Beban {utilization:.0f}% melebihi kapasitas. "
                         "Batasi order baru atau tambah bantuan sementara."))
    elif utilization >= UTIL_WARNING:
        recs.append(("warning",
                     f"Beban {utilization:.0f}% mendekati kapasitas. "
                     "Siapkan staff cadangan dan beri tahu pelanggan estimasi waktu."))

    if slow_bad and utilization < UTIL_WARNING:
        recs.append(("warning",
                     f"{stats['slow_ratio']:.0%} order lambat padahal beban rendah. "
                     "Periksa alur kerja/SOP, bukan jumlah staff."))

    for name, d in stats["by_bartender"].items():
        if d["done"] >= MIN_FINISHED_FOR_STATS and d["slow"] / d["done"] > 0.5:
            recs.append(
                ("info", f"Order {name} sering lambat. Cek distribusi tugas atau beri pendampingan."))

    if not reliable:
        recs.append(("info", f"Data layanan baru {stats['finished']} order selesai; "
                     f"rekomendasi SDM lebih akurat setelah ≥ {MIN_FINISHED_FOR_STATS}."))
    if not recs:
        recs.append(
            ("ok", "Operasional normal. Tidak ada tindakan diperlukan."))
    return recs


def alert_level(recs):
    levels = [r[0] for r in recs]
    for lv in ("critical", "warning"):
        if lv in levels:
            return lv
    return None


# ------------------------------------------------------------
# ALERT WHATSAPP KE MANAJER
# ------------------------------------------------------------
def build_alert_message(level, summary, stats, recs):
    icon = "🔴 KRITIS" if level == "critical" else "🟠 PERINGATAN"
    lines = [
        f"{icon} — Natto Milk",
        f"Staff aktif: {summary['active_staff']}/{summary['total_staff']}",
        f"Beban: {summary['workload']} / kapasitas {summary['capacity']} "
        f"({summary['utilization']:.0f}%)",
        f"Order: {stats['on_time']} tepat waktu, {stats['slow']} lambat, "
        f"{stats['in_progress']} diproses",
        "",
        "Rekomendasi:",
    ]
    lines += [f"- {text}" for lv,
              text in recs if lv in ("critical", "warning")]
    return "\n".join(lines)


def should_send(last_sent_iso, last_level, level):
    """Kirim bila level naik, atau cooldown sudah lewat."""
    if level is None:
        return False
    if last_sent_iso is None:
        return True
    rank = {"warning": 1, "critical": 2}
    if rank.get(level, 0) > rank.get(last_level, 0):
        return True
    minutes = _minutes(last_sent_iso, now_iso())
    return minutes is not None and minutes >= ALERT_COOLDOWN_MIN


def manual_whatsapp_link(phone, message):
    phone = "".join(ch for ch in str(phone) if ch.isdigit())
    return f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"


def send_whatsapp_alert(phone, message):
    """
    Kirim otomatis lewat gateway Fonnte bila FONNTE_TOKEN valid di .env.
    Token kosong / "0" → return link wa.me (kirim manual).
    Return: (ok: bool, info: str)
    """
    token = os.getenv("FONNTE_TOKEN", "").strip().strip('"').strip("'")
    if token in ("", "0"):
        return False, manual_whatsapp_link(phone, message)
    try:
        import requests
        resp = requests.post(
            "https://api.fonnte.com/send",
            headers={"Authorization": token},
            data={"target": phone, "message": message},
            timeout=15,
        )
        # Fonnte bisa membalas HTTP 200 walau gagal; cek field "status" di body
        try:
            body = resp.json()
        except ValueError:
            return False, f"Respons tidak dikenali: {resp.text[:200]}"
        if resp.ok and body.get("status") is True:
            return True, "terkirim"
        return False, f"Fonnte menolak: {body.get('reason', resp.text[:200])}"
    except Exception as exc:  # jaringan/timeout
        return False, f"Gagal kirim: {exc}"
