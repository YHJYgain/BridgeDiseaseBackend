import cv2
import numpy as np
from flask import current_app
from skimage.morphology import skeletonize

from app.constants import DiseaseGrade


def compute_count(masks):
    """计算病害数量（通用）"""
    return masks.shape[0]


def compute_perimeter(masks):
    """计算病害总周长（通用）"""
    contours, _ = cv2.findContours(masks, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total_perimeter = sum(cv2.arcLength(cnt, closed=True) for cnt in contours)
    return float(total_perimeter)


def compute_area(masks):
    """计算病害总面积（通用）"""
    return float(np.sum(masks))


def compute_shape_complexity(perimeter, area):
    """计算形状复杂度（通用）"""
    if perimeter == 0:  # 避免除零错误
        return 0.0
    return float(1 - (4 * np.pi * area) / (perimeter ** 2))


def compute_texture_roughness(masks):
    """计算纹理粗糙度，使用 Laplacian 变换后的标准差（通用）"""
    # 将掩码转换为灰度图像（0 和 1 转换到 0 和 255）
    gray_mask = (masks * 255).astype(np.uint8)
    # 计算 Laplacian 变换结果
    laplacian = cv2.Laplacian(gray_mask, cv2.CV_64F)
    # 计算 Laplacian 值的标准差作为纹理粗糙度
    texture_roughness = np.std(laplacian)
    return float(texture_roughness)


def compute_crack_width(masks):
    """计算裂缝宽度（仅针对裂缝）"""
    # 骨架化
    skeleton = skeletonize(masks.astype(bool))
    # 距离变换
    dist_transform = cv2.distanceTransform((masks * 255).astype(np.uint8), cv2.DIST_L2, 5)
    crack_widths = dist_transform[skeleton]
    return float(2 * np.median(crack_widths)) if crack_widths.size > 0 else 0.0


def compute_avg_hue(masks, image):
    """计算平均色调（仅针对锈蚀）"""
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue_values = hsv_image[masks == 1, 0]  # 取病害区域的 hue 通道
    if hue_values.size == 0:
        return 0.0
    H_max = 179  # OpenCV HSV 色调最大值
    adjusted_hue = H_max - np.median(hue_values)
    return float(adjusted_hue)


def min_max_normalize(value, min_value, max_value):
    """ 归一化函数，使数据在 0 到 1 之间 """
    if max_value == min_value:
        return 0  # 避免除零错误
    return (value - min_value) / (max_value - min_value)


def evaluate_disease_severity(disease_count, disease_perimeter, disease_area, shape_complexity, texture_roughness,
                              crack_width, avg_hue, media):
    """
    根据病害的多个指标，计算病害严重性分数和病害等级（轻度、中度、重度、严重）。

    :param disease_count: 病害数量
    :param disease_perimeter: 病害周长
    :param disease_area: 病害面积
    :param shape_complexity: 形状复杂度
    :param texture_roughness: 纹理粗糙度
    :param crack_width: 裂缝宽度
    :param avg_hue: 平均色调
    :param media: 媒体
    :return: 病害严重性分数和病害等级（轻度、中度、重度、严重）
    """

    # 读取指标权重配置
    weights = current_app.config['DISEASE_INDEX_WEIGHTS']

    # 读取裂缝缩放因子配置
    scale_factor = current_app.config['CRACK_SCALA_FACTOR']

    # 动态计算各指标最大值
    max_disease_count = (media.resolution_width * media.resolution_height * disease_count) // disease_area \
        if disease_area else 0
    max_disease_perimeter = float((2 * (media.resolution_width + media.resolution_height)))
    max_disease_area = float(media.resolution_width * media.resolution_height)
    max_crack_width = float(min(media.resolution_width, media.resolution_height) / scale_factor)
    min_max_values = {
        'disease_count': (0, max_disease_count),
        'disease_perimeter': (0.0, max_disease_perimeter),
        'disease_area': (0.0, max_disease_area),
        'shape_complexity': (0.0, 1.0),
        'texture_roughness': (0.0, 65025.0),
        'crack_width': (0.0, max_crack_width),
        'avg_hue': (0.0, 180.0)
    }

    # 构造一个参数字典，确保所有需要的键都在其中
    params = {
        'disease_count': disease_count,
        'disease_perimeter': disease_perimeter,
        'disease_area': disease_area,
        'shape_complexity': shape_complexity,
        'texture_roughness': texture_roughness,
        'crack_width': crack_width,
        'avg_hue': avg_hue,
    }

    # 归一化
    normalized_values = {
        key: min_max_normalize(params[key], *min_max_values[key])
        for key in weights.keys()
    }

    # 计算加权总分
    weighted_score = sum(normalized_values[key] * weights[key] for key in weights)

    # 根据得分确定病害等级和描述
    if weighted_score >= 0.8:
        return weighted_score, DiseaseGrade.CRITICAL.value, '病害情况严重，需要立即采取修复措施。'
    elif weighted_score >= 0.5:
        return weighted_score, DiseaseGrade.SEVERE.value, '病害情况重度，应尽快安排修复。'
    elif weighted_score >= 0.2:
        return weighted_score, DiseaseGrade.MODERATE.value, '病害情况中等，应安排维护。'
    else:
        return weighted_score, DiseaseGrade.MILD.value, '病害情况轻微，定期观察即可。'
