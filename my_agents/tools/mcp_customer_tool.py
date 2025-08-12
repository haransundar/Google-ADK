# my_agents/tools/mcp_customer_tool.py
import requests

# This is a standard Python function that acts as a tool.
# All tool errors must be returned as {"error": "..."} for consistency.
def customer_lookup(customer_id: str) -> dict:
    """
    Retrieves internal details for a given customer ID by calling the customer data server.
    Use this to get a customer's risk score, recent activity, and profile info.
    """
    url = "http://localhost:8001/tools/get_customer_details/invoke"
    payload = {"customer_id": customer_id}
    print(f"Tool: Calling customer data server for {customer_id}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        output = response.json().get("output", {})
        if not output:
            return {"error": "Customer not found."}
        return output
    except requests.exceptions.RequestException as e:
        print(f"Error calling customer data server: {e}")
        return {"error": f"Could not connect to customer data server: {e}"}