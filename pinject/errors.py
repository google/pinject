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

    def __init__(self, injection_site_desc, binding_key, bindings):
        Error.__init__(
            self, 'when injecting {0}, {1} ambiguously refers to any'
            ' of:\n{2}'.format(
                injection_site_desc, binding_key, '\n'.join(
                    '  {0}'.format(b.get_binding_target_desc_fn())
                    for b in bindings)))


class BadDependencyScopeError(Error):

    def __init__(self, injection_site_desc,
                 from_scope_id, to_scope_id, binding_key):
        Error.__init__(
            self, 'when injecting {0} in {1}, scope {2} is not usable from'
            ' scope {3}'.format(
                binding_key, injection_site_desc, to_scope_id, from_scope_id))


class ConfigureMethodMissingArgsError(Error):

    def __init__(self, configure_fn, possible_args):
        Error.__init__(
            self, 'binding spec method {0} must have at least'
            ' one of the expected args {1}'.format(
                locations.get_name_and_loc(configure_fn), possible_args))


class ConflictingExplicitBindingsError(Error):

    def __init__(self, colliding_bindings):
        Error.__init__(
            self, 'multiple explicit bindings for same binding name:\n'
            '{0}'.format('\n'.join('  {0}'.format(b)
                                   for b in colliding_bindings)))


class ConflictingRequiredBindingError(Error):

    def __init__(self, required_binding, colliding_bindings):
        Error.__init__(
            self, 'conflicting implicit bindings for binding required at {0}'
            ' for {1}:\n{2}'.format(
                required_binding.require_loc, required_binding.binding_key,
                '\n'.join('  {0}'.format(b) for b in colliding_bindings)))


class CyclicInjectionError(Error):

    def __init__(self, binding_stack):
        Error.__init__(
            self, 'cyclic injections:\n{0}'.format(
                '\n'.join('  {0}'.format(b) for b in binding_stack)))


class DecoratorAppliedToNonInitError(Error):

    def __init__(self, decorator_name, fn):
        Error.__init__(
            self, '@{0} cannot be applied to non-initializer {1}'.format(
                decorator_name, locations.get_name_and_loc(fn)))


class DirectlyPassingInjectedArgsError(Error):

    def __init__(self, duplicated_args, injection_site_desc, provider_fn):
        Error.__init__(
            self, 'somewhere in {0}, injected args {1} passed directly when'
            ' calling {2}'.format(
                injection_site_desc, list(duplicated_args),
                locations.get_name_and_loc(provider_fn)))


class DuplicateDecoratorError(Error):

    def __init__(self, decorator_name, second_decorator_loc):
        Error.__init__(
            self, 'at {0}, @{1} cannot be applied twice'.format(
                second_decorator_loc, decorator_name))


class EmptyBindingSpecError(Error):

    def __init__(self, binding_spec):
        Error.__init__(
            self, 'binding spec {0} at {1} must have either a configure()'
            ' method or a provider method but has neither'.format(
                binding_spec.__class__.__name__,
                locations.get_loc(binding_spec.__class__)))


class EmptyProvidesDecoratorError(Error):

    def __init__(self, at_provides_loc):
        Error.__init__(
            self, '@provides() at {0} needs at least one non-default'
            ' arg'.format(at_provides_loc))


class EmptySequenceArgError(Error):

    def __init__(self, call_site_loc, arg_name):
        Error.__init__(
            self, 'expected non-empty sequence arg {0} at {1}'.format(
                arg_name, call_site_loc))


class InjectingNoneDisallowedError(Error):

    def __init__(self, proviser_desc):
        Error.__init__(
            self, 'cannot inject None (returned from {0}) because'
            ' allow_injecting_none=False'.format(proviser_desc))


class InvalidBindingTargetError(Error):

    def __init__(self, binding_loc, binding_key, binding_target,
                 expected_type_str):
        Error.__init__(
            self, '{0} cannot be bound to {1} at {2} because the latter is of'
            ' type {3}, not {4}'.format(
                binding_key, binding_target, binding_loc,
                type(binding_target).__name__, expected_type_str))


class MissingRequiredBindingError(Error):

    def __init__(self, required_binding):
        Error.__init__(
            self, 'at {0}, binding required for {1}, but no such binding was'
            ' ever created'.format(required_binding.require_loc,
                                   required_binding.binding_key))


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


class NoRemainingArgsToInjectError(Error):

    def __init__(self, decorator_loc):
        Error.__init__(
            self, 'at {0}, all args are declared passed directly and therefore'
            ' no args will be injected; call the method directly'
            ' instead?'.format(decorator_loc))


class NoSuchArgError(Error):

    def __init__(self, call_site_loc, arg_name):
        Error.__init__(self, 'at {0}, no such arg named {1}'.format(
            call_site_loc, arg_name))


# TODO(kurts): replace NoSuchArgToInjectError with NoSuchArgError.
class NoSuchArgToInjectError(Error):

    def __init__(self, decorator_loc, arg_binding_key, fn):
        Error.__init__(
            self, 'cannot inject {0} into {1} at {2}: no such arg name'.format(
                arg_binding_key, fn.__name__, decorator_loc))


class NonExplicitlyBoundClassError(Error):

    def __init__(self, provide_loc, cls):
        Error.__init__(
            self, 'at {0}, cannot instantiate class {1}, since it is not'
            ' explicitly marked as injectable and only_use_explicit_bindings'
            ' is set to True'.format(provide_loc, cls.__name__))


class NothingInjectableForArgError(Error):

    def __init__(self, binding_key, injection_site_desc):
        Error.__init__(
            self, 'when injecting {0}, nothing injectable for {1}'.format(
                injection_site_desc, binding_key))


class OnlyInstantiableViaProviderFunctionError(Error):

    def __init__(self, injection_site_fn, arg_binding_key, binding_target_desc):
        Error.__init__(
            self, 'when injecting {0}, {1} cannot be injected, because its'
            ' provider, {2}, needs at least one directly passed arg'.format(
                locations.get_name_and_loc(injection_site_fn),
                arg_binding_key, binding_target_desc))


class OverridingDefaultScopeError(Error):

    def __init__(self, scope_id):
        Error.__init__(
            self, 'cannot override default scope {0}'.format(scope_id))


class PargsDisallowedWhenCopyingArgsError(Error):

    def __init__(self, decorator_name, fn, pargs_arg_name):
        Error.__init__(
            self, 'decorator @{0} cannot be applied to {1} with *{2}'.format(
                decorator_name, locations.get_name_and_loc(fn), pargs_arg_name))


class TooManyArgsToInjectDecoratorError(Error):

    def __init__(self, decorator_loc):
        Error.__init__(
            self, 'at {0}, cannot specify both arg_names and'
            ' all_except'.format(decorator_loc))


class UnknownScopeError(Error):

    def __init__(self, scope_id, binding_loc):
        Error.__init__(self, 'unknown scope ID {0} in binding created at'
                       ' {1}'.format(scope_id, binding_loc))


class WrongArgElementTypeError(Error):

    def __init__(self, arg_name, idx, expected_type_desc, actual_type_desc):
        Error.__init__(
            self, 'wrong type for element {0} of arg {1}: expected {2} but got'
            ' {3}'.format(idx, arg_name, expected_type_desc, actual_type_desc))


class WrongArgTypeError(Error):

    def __init__(self, arg_name, expected_type_desc, actual_type_desc):
        Error.__init__(
            self, 'wrong type for arg {0}: expected {1} but got {2}'.format(
                arg_name, expected_type_desc, actual_type_desc))
