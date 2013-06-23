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


from . import binding_keys
from . import provider_indirections


class ArgBindingKey(object):
    """The binding key for an arg of a function."""

    def __init__(self, arg_name, binding_key, provider_indirection):
        self._arg_name = arg_name
        self.binding_key = binding_key
        self.provider_indirection = provider_indirection

    def __repr__(self):
        return '<{0}>'.format(self)

    def __str__(self):
        return 'the arg named "{0}" {1}'.format(
            self._arg_name, self.binding_key.annotation_as_adjective())

    def __eq__(self, other):
        return (isinstance(other, ArgBindingKey) and
                self._arg_name == other._arg_name and
                self.binding_key == other.binding_key and
                self.provider_indirection == other.provider_indirection)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        # Watch out: self._arg_name is likely also binding_key._name, and so
        # XORing their hashes will remove the arg name from the hash.
        # self._arg_name is really captured as part of the other two, so let's
        # omit it.
        return (hash(self.binding_key) ^
                hash(self.provider_indirection))

    # TODO(kurts): the methods feel unbalanced: they only use self._arg_name.
    # That should probably be a full-fledged class, and ArgBindingKey should
    # just have two public attributes?

    def can_apply_to_one_of_arg_names(self, arg_names):
        """Returns whether this object can apply to one of the arg names."""
        return self._arg_name in arg_names

    def conflicts_with_any_arg_binding_key(self, arg_binding_keys):
        """Returns whether this arg binding key conflicts with others.

        One arg binding key conflicts with another if they are for the same
        arg name, regardless of whether they have the same annotation (or lack
        thereof).

        Args:
          arg_binding_keys: a sequence of ArgBindingKey
        Returns:
          True iff some element of arg_binding_keys is for the same arg name
              as this binding key
        """
        return self._arg_name in [abk._arg_name for abk in arg_binding_keys]


# TODO(kurts): Get a second opinion on module-level methods operating on
# internal state of classes.  In another language, this would be a static
# member and so allowed access to internals.
def get_unbound_arg_names(arg_names, arg_binding_keys):
    """Determines which args have no arg binding keys.

    Args:
      arg_names: a sequence of the names of possibly bound args
      arg_binding_keys: a sequence of ArgBindingKey each of whose arg names is
          in arg_names
    Returns:
      a sequence of arg names that is a (possibly empty, possibly non-proper)
          subset of arg_names

    """
    bound_arg_names = [abk._arg_name for abk in arg_binding_keys]
    return [arg_name for arg_name in arg_names
            if arg_name not in bound_arg_names]


def create_kwargs(arg_binding_keys, provider_fn):
    """Creates a kwargs map for the given arg binding keys.

    Args:
      arg_binding_keys: a sequence of ArgBindingKey for some function's args
      provider_fn: a function that takes an ArgBindingKey and returns whatever
          is bound to that binding key
    Returns:
      a (possibly empty) map from arg name to provided value
    """
    return {arg_binding_key._arg_name: provider_fn(arg_binding_key)
            for arg_binding_key in arg_binding_keys}


_PROVIDE_PREFIX = 'provide_'
_PROVIDE_PREFIX_LEN = len(_PROVIDE_PREFIX)


def new(arg_name, annotated_with=None):
    """Creates an ArgBindingKey.

    Args:
      arg_name: the name of the bound arg
      annotation: an Annotation, or None to create an unannotated arg binding
          key
    Returns:
      a new ArgBindingKey
    """
    if arg_name.startswith(_PROVIDE_PREFIX):
        binding_key_name = arg_name[_PROVIDE_PREFIX_LEN:]
        provider_indirection = provider_indirections.INDIRECTION
    else:
        binding_key_name = arg_name
        provider_indirection = provider_indirections.NO_INDIRECTION
    binding_key = binding_keys.new(binding_key_name, annotated_with)
    return ArgBindingKey(arg_name, binding_key, provider_indirection)
