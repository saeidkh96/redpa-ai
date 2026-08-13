from redpa_sdk import RedPA

with RedPA() as client:
    pending = client.reviews(status="pending", limit=10)
    for review in pending.get("items", []):
        print(review["id"], review["reason"])
