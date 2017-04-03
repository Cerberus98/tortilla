import os

from tortilla import exception

# Patterns I may support:
# ======================
# conf.get("a.b.c")
# conf.get("a_b_c")
# with conf.section("a.b") as cfg:
#   cfg.get("c")
# conf.get("a").get("b").get("c")
# conf.a.b.c

# Always lower case access
# Legit scoping -> a.b.c
# Optional Scoping by inferring modules
# web.service.hostname, web.service.port

# TODO
# Be able to introspect a project and find all of the config
#   * From that, be able to look at the environment and tell what things are
#     undefined and validate the ones that are
#   * Also be able to generate a template file of *all* of the application
#     variables and spit it out so it's easy to maintain
#   * Ideally this is just an entry point you can define with the project
#     by importing Tortilla
# * Define validations for variables
# * Required variables
# * Optional variables
# * Override variables without losing the original config in process
# * inspect/store modules and lines for imports so if you hit a conflict
#   between two modulesit's easy to resolve
# * Be able to specify overrides in a way that doesn't involve arcane trickery
#   * I don't know what this looks like. You can't guarantee the loading order
#     of modules exactly.
# * Somehow solve the load order problem. This file won't be loaded until
#   something imports it to use it. If the primary application doesn't
#   need config then there's no much we can do about it just being a module
#   * Could be an explicit hook if the user wants best-effort loading. Something
#     explicit in an entrypoint?
#   * Ideally we could find a way so it's always loaded no matter what. If you
#     write it into the function that starts the webserver, then a separate
#     hook that wants to open a shell with app things sourced and imported
#     also needs those values loaded apriori
# * Could always define different modes. Strict requires you to define everything
#   whereas lazy works like the original implementation and just sucks things in
#   from the env vars when they're found

class Var(object):
    def __init__(self, name, value, required=False, default=False):
        if required and default:
            raise exception.ConfigNecessityConflict(key=name)

        self._name
        self._required = required
        self._default = default
        self._value = None
        self._override_value = None
        self._override_defined = False
        self._defined = False

    @property
    def required(self):
        return self._required

    @property
    def default(self):
        return self._default

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        if not self._defined:
            raise exception.ConfigUndefined(key=self._name)
        if self._override_defined:
            return self._override_value
        return self._value

    def set_value(self, value):
        if self._value:
            raise exception.ConfigAlreadyDefined(key=self._name,
                                                 value=self._value)
        self._defined = True
        self._value = value

    def set_override(self, value):
        if self._override_defined:
            raise exception.ConfigAlreadyOverridden(key=self._name,
                                                    value=self._override_value,
                                                    original=self._value)
        self._override_value = value
        self._override_defined = True

    def clear_override(self):
        if not self._override_defined:
            raise exception.ConfigNotOverridden(key=self._name)
        self._override_defined = False
        self._override_value = None


class Namespace(object):
    """
    Represents a mapping of dotted namespace to variable names. Exists
    as as top level structure stored by the Config map instead of
    hierarchically nested. All namespaces will be best-effort pre-populated
    at program load time, with an exception for any components loaded
    dynamically by the host application."""

    def __init__(self, name):
        self._name = name
        self._variables = {}

    @property
    def name(self):
        return self._name

    def get(self, key):
        if key not in self._varables:
            raise exception.ConfigUndeclared(key=key, namespace=self._name)
        return self._variables[key].value


class Config(object):
    # TODO There should be no defaults here. They should be definable by the
    #      modules that actually want them

    def __init__(self):
        # TODO
        # * Walk os.environ and set well known key spaces
        # * Be able to have namespaced keys we can fetch
        #   i.e. flask.templates.path
        # * If we could set config overrides without losing the original start
        #   value, that would be awesome.
        # * If we could get a complete debug config map from the app easily at
        #   any time, that would also be delightful
        # * Also note env vars can't be dotted, but underscores
        #   could be stand-ins for dotted namespacing
        # * Lastly, certain keyspaces should probably be removed
        #   from the name: APP_PORT=5000 -> app.port=5000
        self._cfg = {}
        for key, default in self.DEFAULTS.items():
            if key in os.environ:
                default = os.environ[key]
            if key in self._cfg:
                raise exception.ConfigConflict(key=key, value=self._cfg[key])
            self._cfg.setdefault(key, default)

    def get(self, key, default=None):
        if key not in self._cfg:
            env_key = ('_'.join(key.split('.'))).upper()
            if env_key not in os.environ:
                if default:
                    return default
                raise exception.ConfigKeyNotFound(key=key)
            else:
                # Lazily populate the config
                # TODO These should be enforced by the module explicitly.
                #      instead of deferring to the environment. Why? Because
                #      if we have a bad config we should fail early. What's
                #      that mean? We should also do validation
                self._cfg[key] = os.environ[env_key]
        return self._cfg[key]


CONF = Config()
