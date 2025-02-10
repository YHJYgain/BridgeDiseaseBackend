from flask import request


def get_pagination_params(default_page=1, default_per_page=5):
    """通用分页参数获取函数"""
    page = request.args.get('page', default_page, type=int)
    per_page = request.args.get('per_page', default_per_page, type=int)
    return page, per_page

def adjust_page_if_needed(query, page, per_page):
    """如果请求的页码大于总页数，调整为最后一页"""
    operations_total = query.count()
    pages = (operations_total // per_page) + (1 if operations_total % per_page > 0 else 0)
    if page > pages:
        page = pages
    return page, operations_total, pages
