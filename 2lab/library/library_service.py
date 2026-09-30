class LibraryService:
    def issue_book(self, book, loan):
        book.issue()
        return loan