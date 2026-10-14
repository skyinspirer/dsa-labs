class LibraryService:
    def issue_book(self, book, loan):
        book.issue()
        loan.issue()
        return loan

    def restore_book(self, book, loan, return_date):
        loan.return_book(return_date)
        book.return_copy()
        return loan