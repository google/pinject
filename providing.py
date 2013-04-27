
_PROVIDER_FN_PREFIX = 'provide_'


def default_get_arg_names_from_provider_fn_name(provider_fn_name):
    if provider_fn_name.startswith(_PROVIDER_FN_PREFIX):
        return [provider_fn_name[len(_PROVIDER_FN_PREFIX):]]
    else:
        return []
