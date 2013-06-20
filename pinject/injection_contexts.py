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


from . import errors
from . import scoping


class InjectionContextFactory(object):
    """A creator of _InjectionContexts."""

    def __init__(self, is_scope_usable_from_scope_fn):
        """Initializer.

        Args:
          is_scope_usable_from_scope_fn: a function taking two scope IDs and
              returning whether an object in the first scope can be injected
              into an object from the second scope
        """
        self._is_scope_usable_from_scope_fn = is_scope_usable_from_scope_fn

    def new(self):
        """Creates a _InjectionContext.

        Returns:
          a new empty _InjectionContext in the default scope
        """
        return _InjectionContext(
            binding_key_stack=[], scope_id=scoping.UNSCOPED,
            is_scope_usable_from_scope_fn=self._is_scope_usable_from_scope_fn)


class _InjectionContext(object):
    """The context of dependency-injecting some bound value."""

    def __init__(self, binding_key_stack, scope_id,
                 is_scope_usable_from_scope_fn):
        """Initializer.

        Args:
          binding_key_stack: a sequence of the binding keys for the bindings
              whose use in injection is in-progress, from the highest level
              (first) to the current level (last)
          scope_id: the scope ID of the current (last) binding's scope
          is_scope_usable_from_scope_fn: a function taking two scope IDs and
              returning whether an object in the first scope can be injected
              into an object from the second scope
        """
        self._binding_key_stack = binding_key_stack
        self._scope_id = scope_id
        self._is_scope_usable_from_scope_fn = is_scope_usable_from_scope_fn

    def get_child(self, binding):
        """Creates a child injection context.

        A "child" injection context is a context for a binding used to
        inject something into the current binding's provided value.

        Args:
          binding: a Binding
        Returns:
          a new _InjectionContext
        """
        child_binding_key = binding.binding_key
        child_scope_id = binding.scope_id
        new_binding_key_stack = self._binding_key_stack + [child_binding_key]
        if child_binding_key in self._binding_key_stack:
            raise errors.CyclicInjectionError(new_binding_key_stack)
        if not self._is_scope_usable_from_scope_fn(
                child_scope_id, self._scope_id):
            raise errors.BadDependencyScopeError(
                self._scope_id, child_scope_id, child_binding_key)
        return _InjectionContext(new_binding_key_stack, child_scope_id,
                                 self._is_scope_usable_from_scope_fn)
