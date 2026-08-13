from redpa_sdk import RedPA

with RedPA() as client:
    print(client.health())
    print(client.agents())
