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
# Define validations for variables
# Required variables
# Optional variables
# Override variables without losing the original config in process

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
