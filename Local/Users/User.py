class User:
    id = None
    balance = None

    def __init__(self, id, balance=None):
        self.id = id
        self.balance = balance

    def save(self):
        return

    def isPresent(self):
        return

    def _create(self):
        return
    # Saves the user into the user DB (creates or updates)
    def _update(self):
        return