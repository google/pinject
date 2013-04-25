
import threading

import errors


class _SingletonScopeId(object):
    def __str__(self):
        return 'singleton scope'
SINGLETON = _SingletonScopeId()


class _PrototypeScopeId(object):
    def __str__(self):
        return 'prototype scope'
PROTOTYPE = _PrototypeScopeId()


DEFAULT_SCOPE = SINGLETON
_BUILTIN_SCOPES = [SINGLETON, PROTOTYPE]


class Scope(object):

    def provide(self, binding_key, default_provider_fn):
        raise NotImplementedError()


class PrototypeScope(object):

    def provide(self, binding_key, default_provider_fn):
        return default_provider_fn()


class SingletonScope(object):

    def __init__(self):
        self._binding_key_to_instance = {}
        self._providing_binding_keys = set()
        # The lock is re-entrant so that default_provider_fn can provide
        # something else in singleton scope.
        self._rlock = threading.RLock()

    def provide(self, binding_key, default_provider_fn):
        with self._rlock:
            try:
                return self._binding_key_to_instance[binding_key]
            except KeyError:
                instance = default_provider_fn()
                self._binding_key_to_instance[binding_key] = instance
                return instance


class _UnscopedScopeId(object):
    def __str__(self):
        return 'unscoped scope'
UNSCOPED = _UnscopedScopeId()


def get_id_to_scope_with_defaults(id_to_scope=None):
    if id_to_scope is not None:
        for scope_id in _BUILTIN_SCOPES:
            if scope_id in id_to_scope:
                raise errors.OverridingDefaultScopeError(scope_id)
        id_to_scope = dict(id_to_scope)
    else:
        id_to_scope = {}
    id_to_scope[PROTOTYPE] = PrototypeScope()
    id_to_scope[SINGLETON] = SingletonScope()
    return id_to_scope


class BindableScopes(object):

    def __init__(self, id_to_scope, is_scope_usable_from_scope_fn):
        self._id_to_scope = id_to_scope
        self._is_scope_usable_from_scope_fn = is_scope_usable_from_scope_fn

    def get_sub_scope(self, binding, binding_context):
        is_scope_id_usable = lambda sid: self._is_scope_usable_from_scope_fn(binding.scope_id, sid)
        if not binding_context.does_scope_id_match(is_scope_id_usable):
            raise errors.BadDependencyScopeError(
                binding.scope_id, binding.binding_key, binding_context)
        return self._id_to_scope[binding.scope_id]
