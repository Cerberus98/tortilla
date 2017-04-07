import itertools
import os
import pkg_resources
import sys

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
    def __init__(self, name, help=None, required=False, default=False):
        if required and default:
            raise exception.ConfigNecessityConflict(key=name)

        self._name = name
        self._namespace = None
        self._required = required
        self._default = default
        self._help = help
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
    def help(self):
        # LOLselfhelp. I should write a book.
        return self._help

    @property
    def namespace(self):
        return self._namespace

    # TODO This is janky. We shouldn't be able to touch the namespace
    #      once it's been set
    @namespace.setter
    def namespace(self, value):
        self._namespace = value

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


class IntVar(Var):
    def set_value(self, value):
        try:
            super().set_value(int(value))
        except TypeError:
            raise exception.ConfigTypeError(value=value, expected_type="Int")


class StrVar(Var):
    def set_value(self, value):
        try:
            super().set_value(str(value))
        except TypeError:
            raise exception.ConfigTypeError(value=value, expected_type="String")


class BoolVar(Var):
    def set_value(self, value):
        try:
            super().set_value(bool(value))
        except TypeError:
            raise exception.ConfigTypeError(value=value, expected_type="Boolean")


class Namespace(object):
    """
    Represents a mapping of dotted namespace to variable names. Exists
    as as top level structure stored by the Config map instead of
    hierarchically nested. All namespaces will be best-effort pre-populated
    at program load time, with an exception for any components loaded
    dynamically by the host application."""

    # TODO Probably override __slots__ here so it's smaller
    def __init__(self, name, prefix):
        self._name = name
        self._prefix = prefix
        if self._prefix:
            self._fqn = "{}.{}".format(self._prefix, self._name)
        else:
            self._fqn = self._name
        self._variables = {}

    @property
    def name(self):
        return self._name

    @property
    def full_namespace(self):
        return self._fqn

    def set_entry(self, name, value):
        self._variables[name] = value

    def get(self, key, context):
        if key not in self._variables:
            env_name = '_'.join(itertools.chain([c.name for c in context], [key])).upper()
            # TODO This is just a POC! This is not the way to do this
            if env_name in os.environ:
                v = Var(key, self)
                v.set_value(os.environ[env_name])
                self.set_entry(key, v)
            else:
                self.set_entry(key, Namespace(key, prefix=self.full_namespace))
        return self._variables[key]

    def __str__(self):
        return self._name

    def __contains__(self, key):
        return key in self._variables

    def __getitem__(self, key):
        return self._variables[key]

# TODO this is a placeholder allows us to hide the fact that a.b.c shouldn't
#      really work
class NamespaceContext(object):
    def __init__(self):
        self._context = []

    def __getattr__(self, key):
        namespace = self._context[-1].get(key, self._context)
        self.add_context(namespace)
        if isinstance(namespace, Var):
            return namespace.value
        return self

    def add_context(self, context):
        self._context.append(context)


class _ConfigBorg(object):
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state

class Config(_ConfigBorg):
    # TODO There should be no defaults here. They should be definable by the
    #      modules that actually want them
    # TODO This should be a Singleton

    def __init__(self, namespace="tortilla"):
        _ConfigBorg.__init__(self)
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
        if "_entrypoint_namespace" not in self.__dict__:
            self._entrypoint_namespace = namespace
        if "_cfg" not in self.__dict__:
            self._cfg = Namespace(namespace, prefix=None)
        # self.load_config_map()
        # self.discover_vars()

    def load_config_map(self):
        # What should we have returned to us here?
        # Other tools expect lists of the actual variable class instances
        for ep in pkg_resources.iter_entry_points(self._entrypoint_namespace):
            ep.load()

    def discover_vars(self):
        pass
        #self._cfg = {}
        #for key, default in self.DEFAULTS.items():
        #    if key in os.environ:
        #        default = os.environ[key]
        #    if key in self._cfg:
        #        raise exception.ConfigConflict(key=key, value=self._cfg[key])
        #    self._cfg.setdefault(key, default)

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
        n_ctx = NamespaceContext()
        n_ctx.add_context(self._cfg[key])
        return n_ctx

    def __getattr__(self, key):
        if key not in self._cfg:
            self._cfg.set_entry(key, Namespace(key, prefix=None))

        n_ctx = NamespaceContext()
        n_ctx.add_context(self._cfg[key])
        return n_ctx

    def register_vars(self, variables, namespace):
        namespace_parts = namespace.split('.')
        current_namespace = self._cfg
        for part in namespace_parts:
            if part not in current_namespace:
                current_namespace.set_entry(
                    part, Namespace(part,
                    prefix=current_namespace.full_namespace))
            current_namespace = current_namespace[part]

        for v in variables:
            v.namepsace = current_namespace
            current_namespace.set_entry(v.name, v)


CONF = Config()
