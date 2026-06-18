from fastapi import HTTPException, status


class FeatureDisabledError(HTTPException):
    def __init__(self, message: str = "Feature is currently disabled"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)


class ConflictError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=message)


class NotFoundError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class PermissionDeniedError(HTTPException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)


class ValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
