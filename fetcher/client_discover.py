from datetime import datetime, MINYEAR

import backoff
import requests
from ratelimit import limits, sleep_and_retry

from fetcher import ini_parser


class TmdbDiscoverClient:
    api_section_name = 'Discover'
    api_options_section_name = f'{api_section_name}.options'
    date_format = '%Y-%m-%d'
    default_path = '/3/discover/movie'

    def __init__(self, config, global_params, options_date=None):
        if options_date is None:
            self.opts = OptionsDate()
        else:
            self.opts = options_date

        self.global_params = global_params
        self.config = config

        self.path = ini_parser.get_value(self.config, TmdbDiscoverClient.api_section_name, 'path',
                                         TmdbDiscoverClient.default_path)

    def discover_movies(self):
        params = ini_parser.get_section_values(self.config, TmdbDiscoverClient.api_options_section_name, True)
        params['language'] = self.global_params.language

        headers = {
            'accept': "application/json",
            'Authorization': f'Bearer {self.global_params.api_key}'
        }

        jsons_lst = []
        for year in range(self.opts.since_year, self.opts.to_year + 1):
            print(f"\rFetching movies of year {year}...", end='', flush=True)
            jsons_lst.append({'year': year, 'content': self.__discover_movies_single_year(params, year, headers=headers)})
        print('\n')
        return jsons_lst

    def __discover_movies_single_year(self, params, year, headers=None):
        date_since = self.opts.date_yearless_since.replace(year=year)
        date_to = self.opts.date_yearless_to.replace(year=year)

        params.update({'release_date.gte': date_since.strftime(TmdbDiscoverClient.date_format),
                       'release_date.lte': date_to.strftime(TmdbDiscoverClient.date_format)})
        return self.__pagination_call(f'{self.global_params.url}{self.path}', params, headers)

    def __pagination_call(self, formatted_url, params, headers=None):
        total_reached = False
        page = 1

        jsons_lst = []
        while not total_reached:
            params['page'] = page
            resp = self.__call_get(formatted_url, params, headers=headers)
            if resp.status_code != 200:
                print(f"report request failed: {resp.status_code} -- {resp.json()}")
                total_reached = True
            else:
                page_json = resp.json()
                jsons_lst.extend(self.__transform(page_json, self.global_params.language))
                if page_json["total_pages"] <= page:
                    total_reached = True
            page = page + 1
        return jsons_lst

    @sleep_and_retry
    @limits(calls=50, period=5)
    @backoff.on_exception(backoff.expo, ValueError, max_tries=10)
    def __call_get(self, formatted_url, params, headers=None):
        resp = requests.get(formatted_url, params, headers=headers)
        if resp.status_code == 429:
            raise ValueError(f"request failed, rate limited: {resp.status_code}")
        elif resp.status_code != 200:
            raise Exception(f"request failed unexpectedly: {resp.status_code} : {resp.text}")
        else:
            return resp

    @staticmethod
    def __transform(json_resp, language):
        new_jsons_lst = []
        for result in json_resp['results']:
            new_json = {'id': result['id'], 'title': result['title'],
                        'link': f'https://www.themoviedb.org/movie/{result['id']}?language={language}',
                        'poster': f'https://image.tmdb.org/t/p/w200/{result['poster_path']}',
                        'original_language': result['original_language'], 'release_date': result['release_date'],
                        'vote_average': result['vote_average'], 'popularity': result['popularity']}
            new_jsons_lst.append(new_json)
        return new_jsons_lst


class OptionsDate:
    def __init__(self, since_year=datetime.now().year, to_year=datetime.now().year,
                 date_yearless_since=datetime(MINYEAR, 1, 1), date_yearless_to=datetime(MINYEAR, 1, 7)):
        self.since_year = since_year
        self.to_year = to_year
        self.date_yearless_since = date_yearless_since
        self.date_yearless_to = date_yearless_to
