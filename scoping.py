

class _SingletonScopeId(object):
    def __str__(self):
        return 'singleton scope'
SINGLETON = _SingletonScopeId()


class _PrototypeScopeId(object):
    def __str__(self):
        return 'prototype scope'
PROTOTYPE = _PrototypeScopeId()


DEFAULT_SCOPES = [SINGLETON, PROTOTYPE]


class Scope(object):

    def provide(self, binding_key, default_provider_fn):
        raise NotImplementedError()


class PrototypeScope(object):

    def provide(self, binding_key, default_provider_fn):
        return default_provider_fn()


class SingletonScope(object):

    def __init__(self):
        self._binding_key_to_instance = {}

    def provide(self, binding_key, default_provider_fn):
        try:
            return self._binding_key_to_instance[binding_key]
        except KeyError:
            instance = default_provider_fn()
            self._binding_key_to_instance[binding_key] = instance
            return instance


UNSCOPED = object()
