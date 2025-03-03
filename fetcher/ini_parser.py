from configparser import NoSectionError, NoOptionError

def get_value(config, section, option, default_if_none=None, fail_if_none=False):
    try:
        value = config.get(section, option)
    except (NoSectionError, NoOptionError) as e:
        if fail_if_none:
            raise e
        value = default_if_none
    return value

def get_section_values(config, section, fail_if_none=False):
    params = {}
    try:
        params.update(config.items(section))
    except NoSectionError as e:
        if fail_if_none:
            raise e
    return params
