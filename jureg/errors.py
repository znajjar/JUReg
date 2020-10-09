class JURegBaseException(Exception):
    pass


class CredentialsNotProvided(JURegBaseException):
    def __str__(self):
        return 'Credentials have to be provided first.'


class WrongDriverArgument(JURegBaseException):
    def __str__(self):
        return 'Driver argument should be either \'ff\' or \'ch\'.'


class CouldNotFinishOperation(JURegBaseException):
    def __str__(self):
        return 'Check your connection.'

