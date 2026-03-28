from collections import defaultdict


_RECEIVER_ACCOUNT_AGE_DAYS = {
    "ACC-999-RECEIVER": 7,
    "ACC-NEW-002": 14,
    "ACC-STABLE-123": 380,
}

_ACCOUNT_REGISTRATION_LOCATION = {
    "ACC-001-SENDER": "Jakarta",
    "ACC-LEGIT-500": "Jakarta",
    "ACC-FAST-777": "Bandung",
}

_SENDER_BASELINE = defaultdict(
    lambda: {"avg_frequency_24h": 2.0, "avg_amount": 5000.0, "txn_count_24h": 2.0},
    {
        "ACC-001-SENDER": {"avg_frequency_24h": 2.0, "avg_amount": 9000.0, "txn_count_24h": 8.0},
        "ACC-LEGIT-500": {"avg_frequency_24h": 3.0, "avg_amount": 700.0, "txn_count_24h": 2.0},
        "ACC-FAST-777": {"avg_frequency_24h": 1.0, "avg_amount": 12000.0, "txn_count_24h": 5.0},
    },
)


def lookup_transaction_context(sender_account: str, receiver_account: str, location: str) -> dict:
    baseline = dict(_SENDER_BASELINE[sender_account])
    return {
        "sender_account": sender_account,
        "receiver_account": receiver_account,
        "receiver_account_age_days": float(_RECEIVER_ACCOUNT_AGE_DAYS.get(receiver_account, 120)),
        "sender_avg_frequency_24h": float(baseline["avg_frequency_24h"]),
        "sender_txn_count_24h": float(baseline["txn_count_24h"]),
        "sender_avg_amount": float(baseline["avg_amount"]),
        "registration_location": _ACCOUNT_REGISTRATION_LOCATION.get(sender_account, location),
    }
