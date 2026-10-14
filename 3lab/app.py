import os
import logging

from datetime import date, datetime
from flask import Flask, jsonify, request

from book import Book
from loan import Loan
from library_value_objects import BookId, ReaderId, LoanPeriod
from library_exceptions import (
    TransitionNotAllowed,
    DomainInvariantViolation,
    InvalidValueObject,
    GatewayUnresolved,
)
from library_repository import InMemoryBookRepository
from loan_repository import InMemoryLoanRepository
from clock import ShiftedClock
from lending_process import LendingProcess


app = Flask(__name__)

book_repository = InMemoryBookRepository()
loan_repository = InMemoryLoanRepository()
clock = ShiftedClock()

process = LendingProcess(
    book_repository,
    clock,
    fine_paid=lambda reader_id: True,
)


def get_loan(loan_id):
    loan = loan_repository.get(loan_id)

    if loan is None:
        return None

    return loan


def loan_to_dict(loan):
    return {
        "id": loan.id,
        "book_id": loan.book_id.value,
        "reader_id": loan.reader_id.value,
        "state": loan.state_name,
        "allowed_events": list(loan.allowed_events),
        "period": {
            "start": loan.period.start.isoformat(),
            "end": loan.period.end.isoformat(),
        },
        "fine": loan.fine.amount,
        "events": [
            {
                "name": event.name,
                "occurred_on": event.occurred_on.isoformat(),
                "details": event.details,
            }
            for event in loan.events
        ],
    }


@app.errorhandler(TransitionNotAllowed)
def handle_transition_error(error):
    return jsonify({
        "error": "transition_not_allowed",
        "message": str(error),
    }), 409


@app.errorhandler(DomainInvariantViolation)
def handle_invariant_error(error):
    return jsonify({
        "error": "domain_invariant_violation",
        "message": str(error),
    }), 422


@app.errorhandler(InvalidValueObject)
def handle_value_error(error):
    return jsonify({
        "error": "invalid_value_object",
        "message": str(error),
    }), 422


@app.errorhandler(ValueError)
def handle_validation_error(error):
    return jsonify({
        "error": "validation_error",
        "message": str(error),
    }), 422


@app.errorhandler(GatewayUnresolved)
def handle_gateway_error(error):
    return jsonify({
        "error": "gateway_unresolved",
        "message": str(error),
    }), 500


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({
        "error": "not_found",
        "message": "Ресурс не найден",
    }), 404


@app.post("/books")
def create_book():
    data = request.get_json(silent=True) or {}

    book_id = int(data["id"])
    title = data["title"]
    copies = int(data["copies"])

    book = Book(BookId(book_id), title, copies)
    book_repository.save(book)

    return jsonify({
        "id": book.id.value,
        "title": book.title,
        "copies": copies,
        "available": book.available,
    }), 201


@app.post("/loans")
def create_loan():
    data = request.get_json(silent=True) or {}

    book_id = BookId(int(data["book_id"]))
    reader_id = ReaderId(int(data["reader_id"]))
    loan_id = int(data["id"])

    if book_repository.get(book_id) is None:
        return jsonify({
            "error": "not_found",
            "message": "Книга не найдена",
        }), 404

    start = date.fromisoformat(data["start"])
    end = date.fromisoformat(data["end"])

    period = LoanPeriod(start, end)
    loan = Loan(loan_id, book_id, reader_id, period)

    loan_repository.save(loan)
    process.reserve_book(loan)

    return jsonify(loan_to_dict(loan)), 201


@app.get("/loans/<int:loan_id>")
def get_loan_state(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена",
        }), 404

    return jsonify(loan_to_dict(loan))


@app.post("/loans/<int:loan_id>/check-reservation")
def check_reservation(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена",
        }), 404

    result = process.check_reservation(loan)

    return jsonify({
        "result": result,
        "loan": loan_to_dict(loan),
    })


@app.post("/loans/<int:loan_id>/issue")
def issue_loan(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена",
        }), 404

    result = process.issue_book(loan)

    return jsonify({
        "result": result,
        "loan": loan_to_dict(loan),
    })


@app.post("/loans/<int:loan_id>/extend")
def extend_loan(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена",
        }), 404

    data = request.get_json(silent=True) or {}
    has_waiting_readers = bool(data.get("has_waiting_readers", False))

    new_end = process.extend_loan(loan, has_waiting_readers)

    loan_repository.save(loan)

    return jsonify({
        "new_end": new_end.isoformat(),
        "loan": loan_to_dict(loan),
    })


@app.post("/loans/<int:loan_id>/return")
def return_loan(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена",
        }), 404

    data = request.get_json(silent=True) or {}
    damage_found = bool(data.get("damage_found", False))

    fine = process.return_book(loan, damage_found)

    return jsonify({
        "fine": fine.amount,
        "loan": loan_to_dict(loan),
    })


@app.post("/loans/<int:loan_id>/check-overdue")
def check_overdue(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена",
        }), 404

    result = process.check_overdue(loan)

    return jsonify({
        "result": result,
        "loan": loan_to_dict(loan),
    })


@app.post("/loans/<int:loan_id>/reminder")
def send_reminder(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена",
        }), 404

    result = process.send_due_reminder(loan)

    return jsonify({
        "result": result,
        "loan": loan_to_dict(loan),
    })


@app.post("/loans/<int:loan_id>/administration")
def send_to_administration(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена",
        }), 404

    result = process.process_long_overdue(loan)

    return jsonify({
        "result": result,
        "loan": loan_to_dict(loan),
    })


@app.post("/internal/tick")
def tick_clock():
    data = request.get_json(silent=True) or {}

    try:
        if data.get("now"):
            new_time = datetime.fromisoformat(data["now"])
            clock.set_time(new_time)

        now = clock.now()

        for loan in loan_repository.get_all():
            process.send_due_reminder(loan)
            process.check_overdue(loan)
            process.process_long_overdue(loan)

        return jsonify({
            "now": now.isoformat(),
            "result": "Время приложения обновлено",
        })

    except ValueError as error:
        return jsonify({
            "error": "validation_error",
            "message": str(error),
        }), 422


@app.route("/loans/<int:loan_id>/cancel", methods=["POST"])
def cancel_loan(loan_id):
    loan = get_loan(loan_id)

    if loan is None:
        return jsonify({
            "error": "not_found",
            "message": "Выдача не найдена"
        }), 404

    loan.cancel("Бронирование отменено")
    return jsonify({"loan": loan_to_dict(loan)})


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper()
)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000"))
    )