class TortillaException(Exception):
    def __init__(self, **keys):
        super().__init__(self.message % keys)


class ConfigKeyNotFound(TortillaException):
    message = ("The requested key '%(key)s' does not exist in the "
               "application configuration")


class ConfigConflict(TortillaException):
    message = ("The requested key '%(key)s' already exists in the config "
               "and has value '%(value)s'")


class ConfigNecessityConflict(TortillaException):
    message = ("The declared variable '%(key)s' may not be both required "
               "and have a default value")


class ConfigAlreadyDefined(TortillaException):
    message = ("The declared variable '%(key)s' has already been defined "
               "and has value '%(value)s'")


class ConfigUndeclared(TortillaException):
    message = ("The variable '%(key)s' has not been declared in namespace "
               "'%(namespace)s'")


class ConfigUndefined(TortillaException):
    message = ("The declared variable '%(key)s' has not been defined")


class ConfigAlreadyOverridden(TortillaException):
    message = ("The declared variable '%(key)s' has already been overridden "
               "with value '%(value)s'. Original value is '%(original)s'")


class ConfigNotOverridden(TortillaException):
    message = ("The declared variable '%(key)s' has not been overridden")


class ConfigTypeError(TortillaException):
    message = ("Value '%(value)s' is not of type %(expected_type)s")
