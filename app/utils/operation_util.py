import time

from flask import current_app, jsonify

from app.constants import OperationStatus
from app.models import db


def handle_operation_failure(failure_message, new_operation, start_time):
    new_operation.duration = time.time() - start_time
    new_operation.failure_message = failure_message
    new_operation.status = OperationStatus.FAILURE
    db.session.add(new_operation)
    db.session.commit()

    current_app.logger.warning(f"operation: {new_operation}")
    return jsonify({'operation': new_operation.to_dict()}), 400
