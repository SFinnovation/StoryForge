from fastapi import HTTPException, status


class StoryForgeError(Exception):
    """应用层业务异常基类。"""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(StoryForgeError):
    def __init__(self, resource: str, resource_id: str | int) -> None:
        super().__init__(
            message=f"{resource} '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


def to_http_exception(exc: StoryForgeError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)
