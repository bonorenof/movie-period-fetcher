from fetcher import ini_parser


class GlobalConfig:
    global_section_name = 'Global'
    default_language = 'en-US'
    default_url = 'https://api.themoviedb.org'

    def __init__(self, config):
        self.url = ini_parser.get_value(config, GlobalConfig.global_section_name, 'url', GlobalConfig.default_url)
        self.api_key = ini_parser.get_value(config, GlobalConfig.global_section_name, 'api_key', fail_if_none=True)
        self.language = ini_parser.get_value(config, GlobalConfig.global_section_name, 'language',
                                             GlobalConfig.default_language)
        self.render_limit = ini_parser.get_value(config, GlobalConfig.global_section_name, 'render_limit', 20)
