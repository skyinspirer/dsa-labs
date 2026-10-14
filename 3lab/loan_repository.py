class InMemoryLoanRepository:
    def __init__(self):
        self._items = {}

    def get(self, loan_id):
        return self._items.get(loan_id)

    def save(self, loan):
        self._items[loan.id] = loan

    def get_all(self):
        return list(self._items.values())