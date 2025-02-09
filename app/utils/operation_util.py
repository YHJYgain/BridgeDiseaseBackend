import time

from app.constants import OperationStatus
from app.models import db


def handle_operation_success(new_operation, start_time, owner_id=None):
    new_operation.duration = time.time() - start_time
    new_operation.status = OperationStatus.SUCCESS
    new_operation.owner_id = owner_id
    db.session.add(new_operation)
    db.session.commit()

    return new_operation


def handle_operation_failure(new_operation, start_time, failure_message, owner_id=None):
    new_operation.duration = time.time() - start_time
    new_operation.failure_message = failure_message
    new_operation.status = OperationStatus.FAILURE
    new_operation.owner_id = owner_id
    db.session.add(new_operation)
    db.session.commit()

    return new_operation
