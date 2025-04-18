import json
from datetime import datetime
from json import JSONEncoder


class DateTimeEncoder(JSONEncoder):
    """
    自定义 JSON 编码器，用于处理 datetime 对象的序列化
    
    在将包含 datetime 对象的数据结构转换为 JSON 字符串时使用此编码器，
    可以正确处理 datetime 对象，将其转换为 ISO 格式的字符串。
    
    示例:
        json.dumps(data, cls=DateTimeEncoder)
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)