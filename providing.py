


_DEFAULT_PROVIDER_FN_PREFIXES = ['new_', 'provide_']


def default_get_arg_names_from_provider_fn_name(provider_fn_name):
    if provider_fn_name.startswith('_'):
        provider_fn_name = provider_fn_name[1:]
    for prefix in _DEFAULT_PROVIDER_FN_PREFIXES:
        if provider_fn_name.startswith(prefix):
            return [provider_fn_name[len(prefix):]]
            break
    else:
        return []
