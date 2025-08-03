# my_agents/tools/internal_data_tool.py

# This file should have NO imports and NO @tool decorator.

MOCK_CUSTOMER_DB = {
    "CUST-007": {
        "name": "John Doe",
        "risk_score": "High",
        "account_open_date": "2022-01-15",
        "recent_activity": "Multiple cash deposits of $9,500 in the last 7 days.",
        "occupation": "Owner, Cash-Intensive Business"
    },
    "CUST-101": {
        "name": "Jane Smith",
        "risk_score": "Low",
        "account_open_date": "2018-05-20",
        "recent_activity": "Regular payroll deposits, occasional bill payments.",
        "occupation": "Software Engineer"
    },
}

# THE FIX: Ensure the function name is exactly "customer_lookup"
# All tool errors must be returned as {"error": "..."} for consistency.
def customer_lookup(customer_id: str) -> dict:
    """
    Retrieves internal details for a given customer ID, including their risk score,
    recent activity, and profile information.
    """
    result = MOCK_CUSTOMER_DB.get(customer_id)
    if not result:
        return {"error": "Customer not found."}
    return result