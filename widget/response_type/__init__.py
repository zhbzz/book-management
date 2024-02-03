from flask import jsonify

class Response:
    def __init__(self, message=None, code=0, **kwargs):
        self.message = message
        self.code = code
        self.data = kwargs

    def add_data(self, **kwargs):
        self.data.update(kwargs)  # 添加额外的键值对

    def json(self):
        return jsonify({
            'message': self.message,
            'code': self.code,
            **self.data,
        })


class SuccessResponse(Response):
    def __init__(self, message="成功", code=200, **kwargs):
        super().__init__(message, code, **kwargs)

class BadRequestResponse(Response):
    def __init__(self, message="请求错误", code=400, **kwargs):
        super().__init__(message, code, **kwargs)

class ErrorResponse(Response):
    def __init__(self, message="错误", code=500, **kwargs):
        super().__init__(message, code, **kwargs)

class NotLoginResponse(Response):
    def __init__(self, message="未登录", code=401, **kwargs):
        super().__init__(message, code, **kwargs)

class DatabaseErrorResponse(Response):
    def __init__(self, message="数据库错误", code=500, **kwargs):
        super().__init__(message, code, **kwargs)

class FormatErrorResponse(Response):
    def __init__(self, message="参数格式错误", code=400, **kwargs):
        super().__init__(message, code, **kwargs)

class NotFoundResponse(Response):
    def __init__(self, message="未找到", code=404, **kwargs):
        super().__init__(message, code, **kwargs)
