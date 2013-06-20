"""Copyright 2013 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import threading

from . import errors


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


# TODO(kurts): either make this class pull its weight, or delete it.
class BindableScopes(object):

    def __init__(self, id_to_scope):
        self._id_to_scope = id_to_scope

    def get_sub_scope(self, binding):
        return self._id_to_scope[binding.scope_id]
