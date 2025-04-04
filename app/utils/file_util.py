import os
from pathlib import Path

import cv2
from PIL import Image
from flask import current_app
from moviepy import VideoFileClip
from werkzeug.utils import secure_filename

from app import Config

# 读取文件类型配置
ALLOWED_IMAGE_EXTENSIONS = Config.ALLOWED_IMAGE_EXTENSIONS
ALLOWED_VIDEO_EXTENSIONS = Config.ALLOWED_VIDEO_EXTENSIONS


def handle_file_upload(file, file_location):
    if not file:
        current_app.logger.warning(f"{file_location} 文件为空")
        return None

    folder = current_app.config[f'{file_location.upper()}_FOLDER']  # 动态获取文件夹配置

    # 确保文件夹存在
    os.makedirs(folder, exist_ok=True)

    # 保存文件
    filename = secure_filename(file.filename)
    file_path = os.path.join('static', file_location, filename)  # 存储相对路径
    file.save(os.path.join(folder, filename))  # 存储文件

    current_app.logger.info(f"{file_location} 文件已保存：{file_path}")
    return file_path


def get_media_info(file_absolute_path):
    file_type = Path(file_absolute_path).suffix[1:].lower()

    file_size = os.path.getsize(file_absolute_path) / 1024  # 文件大小（KB）
    resolution_width = resolution_height = 0  # 默认分辨率为 0
    frame_count = 1  # 默认是图片，帧数为 1

    if file_type in ALLOWED_IMAGE_EXTENSIONS:  # 图片
        with Image.open(file_absolute_path) as img:
            resolution_width, resolution_height = img.size
            frame_count = 1
    elif file_type in ALLOWED_VIDEO_EXTENSIONS:  # 视频
        with VideoFileClip(file_absolute_path) as video:
            resolution_width, resolution_height = video.size
        video = cv2.VideoCapture(file_absolute_path)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))  # 获取视频的帧数
        video.release()  # 释放视频文件
    else:
        current_app.logger.warning(f"获取媒体信息失败，不支持的文件类型：{file_type}")

    return file_size, resolution_width, resolution_height, frame_count


def unify_result_media_format(media, current_user):
    original_result_path = os.path.join('static', 'results', current_user.username, os.path.basename(media.media_path))

    # 根据文件类型更改扩展名
    if media.file_type in ALLOWED_VIDEO_EXTENSIONS:  # 视频文件
        avi_result_path = os.path.splitext(original_result_path)[0] + '.avi'
        new_result_path = os.path.splitext(original_result_path)[0] + '.mp4'  # 默认视频格式为 .mp4

        avi_abs_path = os.path.join(current_app.root_path, avi_result_path)
        new_abs_path = os.path.join(current_app.root_path, new_result_path)

        convert_avi_to_mp4(avi_abs_path, new_abs_path)
    elif media.file_type in ALLOWED_IMAGE_EXTENSIONS:  # 图片文件
        new_result_path = os.path.splitext(original_result_path)[0] + '.jpg'  # 默认图片格式为 .jpg
    else:
        new_result_path = original_result_path

    return new_result_path


def convert_avi_to_mp4(avi_path, mp4_path):
    # 使用 moviepy 读取 avi 文件
    video_clip = VideoFileClip(avi_path)

    # 写入 mp4 格式
    video_clip.write_videofile(mp4_path, codec="libx264")

    # 显式释放资源
    video_clip.close()

    # 删除原 avi 文件
    os.remove(avi_path)
