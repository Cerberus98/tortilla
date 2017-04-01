class TortillaException(Exception):
    def __init__(self, **keys):
        super().__init__(self.message % keys)


class ConfigKeyNotFound(TortillaException):
    message = ("The requested key '%(key)s' does not exist in the "
               "application configuration")


class ConfigConflict(TortillaException):
    message = ("The requested key '%(key)s' already exists in the config "
               "and has value '%(value)s'")
