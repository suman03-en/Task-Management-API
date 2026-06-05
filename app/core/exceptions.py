"""
service layer returns python exceptions so that any interface (e.g. REST API, CLI, etc.) can handle them appropriately and return the correct response to the user.

bad case:
- service layer raises HTTPException with status code and message
- REST API catches HTTPException and returns the status code and message to the user
- but when cli calls service layer, it also catches HTTPException and returns the status code and message to the user, which is not appropriate for CLI

good case:
- service layer raises custom exceptions (e.g. UserAlreadyExistsException, UserNotFoundException, etc.)
- REST API catches custom exceptions and raises HTTPException with appropriate status code and message
- CLI catches custom exceptions and prints appropriate message to the user
"""


class AppBaseException(Exception):
    """Base exception for the application."""
    pass

class UserAlreadyExistsException(AppBaseException):
    """Exception raised when trying to create a user that already exists."""
    pass

class UserNotFoundException(AppBaseException):
    """Exception raised when a user is not found."""
    pass

class TaskNotFoundException(AppBaseException):
    """Exception raised when a task is not found."""
    pass

class ProjectNotFoundException(AppBaseException):
    """Exception raised when a project is not found."""
    pass

class MemberAdditionError(AppBaseException):
    """Exception raised when adding a member to a project fails."""
    pass

class MemberRemovalError(AppBaseException):
    """Exception raised when removing a member from a project fails."""
    pass


