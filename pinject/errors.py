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


import locations


class Error(Exception):
    pass


class AmbiguousArgNameError(Error):

    def __init__(self, binding_key, bindings):
        Error.__init__(
            self, '{0} ambiguously refers to any of:\n{1}'.format(
                binding_key, '\n'.join('  {0}'.format(b.proviser_fn._pinject_desc) for b in bindings)))


class BadDependencyScopeError(Error):

    def __init__(self, from_scope_id, to_scope_id, binding_key):
        Error.__init__(
            self, 'scope "{0}" is not usable when binding {1} from'
            ' "{2}"'.format(to_scope_id, binding_key, from_scope_id))


class ConflictingBindingsError(Error):

    def __init__(self, colliding_bindings):
        Error.__init__(
            self, 'multiple bindings for same binding name:\n{0}'.format(
                '\n'.join('  {0}'.format(b) for b in colliding_bindings)))


class CyclicInjectionError(Error):

    def __init__(self, binding_stack):
        Error.__init__(
            self, 'cyclic injections:\n{0}'.format(
                '\n'.join('  {0}'.format(b) for b in binding_stack)))


class EmptyBindingSpecError(Error):

    def __init__(self, binding_spec):
        Error.__init__(
            self, 'binding spec {0} at {1} must have either a configure()'
            ' method or a provider method but has neither'.format(
                binding_spec.__class__.__name__,
                locations.get_type_loc(binding_spec.__class__)))


class EmptyProvidesDecoratorError(Error):

    def __init__(self, at_provides_loc):
        Error.__init__(
            self, '@provides() at {0} needs at least one non-default'
            ' arg'.format(at_provides_loc))


class InjectableDecoratorAppliedToNonInitError(Error):

    def __init__(self, fn):
        Error.__init__(
            self, '@injectable cannot be applied to non-initializer {0}'.format(
                locations.get_class_name_and_loc(fn)))


class InjectingNoneDisallowedError(Error):

    def __init__(self, proviser_desc):
        Error.__init__(
            self, 'cannot inject None (returned from {0}) because'
            ' allow_injecting_none=False'.format(proviser_desc))


class InvalidBindingTargetError(Error):

    def __init__(self, binding_loc, binding_key, binding_target, expected_type_str):
        Error.__init__(
            self, '{0} cannot be bound to {1} at {2} because the latter is of'
            ' type {3}, not {4}'.format(
                binding_key, binding_target, binding_loc,
                type(binding_target).__name__, expected_type_str))


class MultipleAnnotationsForSameArgError(Error):

    def __init__(self, arg_binding_key, decorator_loc):
        Error.__init__(
            self, 'multiple annotations for {0} at {1}'.format(
                arg_binding_key, decorator_loc))


class MultipleBindingTargetArgsError(Error):

    def __init__(self, binding_loc, binding_key, arg_names):
        Error.__init__(
            self, 'multiple binding target args {0} given for {1} at'
            ' {2}'.format(arg_names, binding_key, binding_loc))


class NoBindingTargetArgsError(Error):

    def __init__(self, binding_loc, binding_key):
        Error.__init__(
            self, 'no binding target arg given for {0} at {1}'.format(
                binding_key, binding_loc))


class NoSuchArgToInjectError(Error):

    def __init__(self, decorator_loc, arg_binding_key, fn):
        Error.__init__(
            self, 'cannot inject {0} into {1} at {2}: no such arg name'.format(
                arg_binding_key, fn.__name__, decorator_loc))


class NonExplicitlyBoundClassError(Error):

    def __init__(self, cls):
        Error.__init__(
            self, 'cannot instantiate class {0}, which is not explicitly'
            ' marked as injectable, when only_use_explicit_bindings is set'
            ' to True'.format(cls.__name__))


class NothingInjectableForArgError(Error):

    def __init__(self, binding_key):
        Error.__init__(
            self, 'there is no injectable class for {0}'.format(binding_key))


class OverridingDefaultScopeError(Error):

    def __init__(self, scope_id):
        Error.__init__(
            self, 'cannot override default scope {0}'.format(scope_id))


class UnknownScopeError(Error):

    def __init__(self, scope_id):
        Error.__init__(self, 'no such scope with ID {0}'.format(scope_id))
