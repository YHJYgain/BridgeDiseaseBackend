from flask import jsonify
from flask_jwt_extended import jwt_required

from app.constants import TaskStatus
from app.decorators import login_required
from app.models import Detection
from app.routes import detection_routes


@detection_routes.route('/statistics', methods=['GET'])
@jwt_required()
@login_required
def get_detection_statistics():
    # 查询检测记录总数
    total_detections = Detection.query.count()

    # 查询不同状态的检测记录数量
    pending_detections = Detection.query.filter(Detection.status == TaskStatus.PENDING).count()
    in_progress_detections = Detection.query.filter(Detection.status == TaskStatus.IN_PROGRESS).count()
    completed_detections = Detection.query.filter(Detection.status == TaskStatus.COMPLETED).count()
    failed_detections = Detection.query.filter(Detection.status == TaskStatus.FAILED).count()

    # 构建统计数据
    detections_statistics = {
        'total': total_detections,
        'pending': pending_detections,
        'in_progress': in_progress_detections,
        'completed': completed_detections,
        'failed': failed_detections
    }

    return jsonify({
        "detections_statistics": detections_statistics,
    }), 200
