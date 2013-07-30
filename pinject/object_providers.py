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


import types

from . import arg_binding_keys
from . import decorators
from . import errors


class ObjectProvider(object):

    def __init__(self, binding_mapping, bindable_scopes, allow_injecting_none):
        self._binding_mapping = binding_mapping
        self._bindable_scopes = bindable_scopes
        self._allow_injecting_none = allow_injecting_none

    def provide_from_arg_binding_key(
            self, injection_site_fn, arg_binding_key, injection_context):
        binding_key = arg_binding_key.binding_key
        binding = self._binding_mapping.get(
            binding_key, injection_context.get_injection_site_desc())
        scope = self._bindable_scopes.get_sub_scope(binding)
        def Provide(*pargs, **kwargs):
            # TODO(kurts): probably capture back frame's file:line for
            # DirectlyPassingInjectedArgsError.
            child_injection_context = injection_context.get_child(
                injection_site_fn, binding)
            provided = scope.provide(
                binding_key,
                lambda: binding.proviser_fn(child_injection_context, self,
                                            pargs, kwargs))
            if (provided is None) and not self._allow_injecting_none:
                raise errors.InjectingNoneDisallowedError(
                    binding.get_binding_target_desc_fn())
            return provided
        provider_indirection = arg_binding_key.provider_indirection
        try:
            provided = provider_indirection.StripIndirectionIfNeeded(Provide)
        except TypeError:
            # TODO(kurts): it feels like there may be other TypeErrors that
            # occur.  Instead, decorators.get_injectable_arg_binding_keys()
            # should probably do all appropriate validation?
            raise errors.OnlyInstantiableViaProviderFunctionError(
                injection_site_fn, arg_binding_key,
                binding.get_binding_target_desc_fn())
        return provided

    def provide_class(self, cls, injection_context,
                      direct_init_pargs, direct_init_kwargs):
        if type(cls.__init__) is types.MethodType:
            init_pargs, init_kwargs = self.get_injection_pargs_kwargs(
                cls.__init__, injection_context,
                direct_init_pargs, direct_init_kwargs)
        else:
            init_pargs = direct_init_pargs
            init_kwargs = direct_init_kwargs
        return cls(*init_pargs, **init_kwargs)

    def call_with_injection(self, provider_fn, injection_context,
                            direct_pargs, direct_kwargs):
        pargs, kwargs = self.get_injection_pargs_kwargs(
            provider_fn, injection_context, direct_pargs, direct_kwargs)
        return provider_fn(*pargs, **kwargs)

    def get_injection_pargs_kwargs(self, fn, injection_context,
                                   direct_pargs, direct_kwargs):
        di_kwargs = arg_binding_keys.create_kwargs(
            decorators.get_injectable_arg_binding_keys(
                fn, direct_pargs, direct_kwargs),
            lambda abk: self.provide_from_arg_binding_key(
                fn, abk, injection_context))
        duplicated_args = set(di_kwargs.keys()) & set(direct_kwargs.keys())
        if duplicated_args:
            raise errors.DirectlyPassingInjectedArgsError(
                duplicated_args, injection_context.get_injection_site_desc(),
                fn)
        all_kwargs = dict(di_kwargs)
        all_kwargs.update(direct_kwargs)
        return direct_pargs, all_kwargs
