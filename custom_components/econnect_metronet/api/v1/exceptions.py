class BaseException(Exception):
    """BaseException used for extension."""

    default_message = "BaseException."

    def __init__(self, message=None):
        self.message = message or self.default_message

    def __str__(self):
        return str(self.message)


class ValidationError(BaseException):
    """Exception raised when a Validator fails."""

    default_message = "Client configuration is invalid."


class QueryNotValid(BaseException):
    """Exception raised when a Query is not valid."""

    default_message = "Query not available."


class ParseError(BaseException):
    """Exception raised when there is an error parsing the response."""

    default_message = "An error occurred while parsing the response. Probably the input is unexpected."


class APIException(BaseException):
    """Exception raised when there is an API error."""

    default_message = "A server error occurred"


class CredentialError(APIException):
    """Exception raised when used credentials are not correct."""

    default_message = "Username or password are not correct"


class MissingToken(APIException):
    """Exception raised when a client is used without prior authentication."""

    default_message = "No token is present. You must authenticate to use the client."


class InvalidToken(APIException):
    """Exception raised when a previously valid token is not valid anymore."""

    default_message = "Used token is not valid. You must authenticate again."


class LockNotAcquired(BaseException):
    """Exception raised when a Lock() is required to run the function."""

    default_message = "System lock not acquired"


class LockError(APIException):
    """Exception raised when it's not possible to obtain the Lock()."""

    default_message = "Unable to obtain the Lock()."


class CodeError(APIException):
    """Exception raised when used panel code is not correct."""

    default_message = "Digited panel code is not correct"


class CommandError(APIException):
    """Exception raised when the API returns an error response after issuing a command."""

    default_message = "An error occurred while executing the command."


class DeviceDisconnectedError(APIException):
    """Exception raised when the device is disconnected."""

    default_message = "Device is disconnected"
