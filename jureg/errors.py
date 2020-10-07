class JURegBaseException(Exception):
    pass


class CredentialsNotProvided(JURegBaseException):
    def __str__(self):
        return 'Credentials have to be provided first.'
