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
from . import locations
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

    def new(self, injection_site_fn):
        """Creates a _InjectionContext.

        Args:
          injection_site_fn: the initial function being injected into
        Returns:
          a new empty _InjectionContext in the default scope
        """
        return _InjectionContext(
            injection_site_fn, binding_stack=[], scope_id=scoping.UNSCOPED,
            is_scope_usable_from_scope_fn=self._is_scope_usable_from_scope_fn)


class _InjectionContext(object):
    """The context of dependency-injecting some bound value."""

    def __init__(self, injection_site_fn, binding_stack, scope_id,
                 is_scope_usable_from_scope_fn):
        """Initializer.

        Args:
          injection_site_fn: the function currently being injected into
          binding_stack: a sequence of the bindings whose use in injection is
              in-progress, from the highest level (first) to the current level
              (last)
          scope_id: the scope ID of the current (last) binding's scope
          is_scope_usable_from_scope_fn: a function taking two scope IDs and
              returning whether an object in the first scope can be injected
              into an object from the second scope
        """
        self._injection_site_fn = injection_site_fn
        self._binding_stack = binding_stack
        self._scope_id = scope_id
        self._is_scope_usable_from_scope_fn = is_scope_usable_from_scope_fn

    def get_child(self, injection_site_fn, binding):
        """Creates a child injection context.

        A "child" injection context is a context for a binding used to
        inject something into the current binding's provided value.

        Args:
          injection_site_fn: the child function being injected into
          binding: a Binding
        Returns:
          a new _InjectionContext
        """
        child_scope_id = binding.scope_id
        new_binding_stack = self._binding_stack + [binding]
        if binding in self._binding_stack:
            raise errors.CyclicInjectionError(new_binding_stack)
        if not self._is_scope_usable_from_scope_fn(
                child_scope_id, self._scope_id):
            raise errors.BadDependencyScopeError(
                self.get_injection_site_desc(),
                self._scope_id, child_scope_id, binding.binding_key)
        return _InjectionContext(
            injection_site_fn, new_binding_stack, child_scope_id,
            self._is_scope_usable_from_scope_fn)

    def get_injection_site_desc(self):
        """Returns a description of the current injection site."""
        return locations.get_name_and_loc(self._injection_site_fn)
