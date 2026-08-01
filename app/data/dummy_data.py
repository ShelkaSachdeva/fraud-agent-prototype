from app.models import Transaction

# -----------------------------------------------------
# Dummy Transactions
# -----------------------------------------------------

transactions = [
    Transaction(
        transaction_id="TXN-1001",
        customer_id="CUST-101",
        amount=12500,
        country="United States",
        merchant="Crypto Exchange",
        is_new_device=True,
        velocity_last_hour=7,
    ),
    Transaction(
        transaction_id="TXN-1002",
        customer_id="CUST-102",
        amount=250,
        country="United States",
        merchant="Amazon",
        is_new_device=False,
        velocity_last_hour=1,
    ),
    Transaction(
        transaction_id="TXN-1003",
        customer_id="CUST-103",
        amount=7200,
        country="United Kingdom",
        merchant="Wire Transfer Service",
        is_new_device=False,
        velocity_last_hour=4,
    ),
    Transaction(
        transaction_id="TXN-1004",
        customer_id="CUST-104",
        amount=180,
        country="Canada",
        merchant="Walmart",
        is_new_device=False,
        velocity_last_hour=1,
    ),
    Transaction(
        transaction_id="TXN-1005",
        customer_id="CUST-105",
        amount=9800,
        country="Singapore",
        merchant="Gift Card Marketplace",
        is_new_device=True,
        velocity_last_hour=6,
    ),
]

# -----------------------------------------------------
# Dummy Customers
# -----------------------------------------------------

customers = {
    "CUST-101": {
        "name": "Alice Johnson",
        "identity_verified": True,
        "sanctions_match": False,
        "customer_risk": "MEDIUM",
    },
    "CUST-102": {
        "name": "Bob Smith",
        "identity_verified": True,
        "sanctions_match": False,
        "customer_risk": "LOW",
    },
    "CUST-103": {
        "name": "Charlie Brown",
        "identity_verified": False,
        "sanctions_match": False,
        "customer_risk": "HIGH",
    },
    "CUST-104": {
        "name": "David Lee",
        "identity_verified": True,
        "sanctions_match": False,
        "customer_risk": "LOW",
    },
    "CUST-105": {
        "name": "Eva Green",
        "identity_verified": True,
        "sanctions_match": True,
        "customer_risk": "HIGH",
    },
}

# -----------------------------------------------------
# Helper Functions
# -----------------------------------------------------

def get_transaction(transaction_id: str):
    """
    Return a transaction by ID.
    """
    for transaction in transactions:
        if transaction.transaction_id == transaction_id:
            return transaction
    return None


def get_customer(customer_id: str):
    """
    Return a customer by customer ID.
    """
    return customers.get(customer_id)