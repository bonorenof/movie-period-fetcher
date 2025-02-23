import configparser
import datetime
import os
import webbrowser
from datetime import datetime, MINYEAR

from fetcher import html_renderer
from fetcher.client_discover import TmdbDiscoverClient, OptionsDate
from fetcher.global_config import GlobalConfig


def __find_ini_files():
    # Scan the current directory for INI files
    ini_files = [f for f in os.listdir('.') if f.lower().endswith('.ini')]
    return ini_files


def __get_ini_file():
    # Find INI files in the current directory
    ini_files = __find_ini_files()

    # Propose the first INI file as default if available
    if ini_files:
        default_ini = ini_files[0]
        ini_file_path = input(f"Please enter the path to the INI file (Press Enter to use '{default_ini}'): ")
        if ini_file_path.strip() == "":
            ini_file_path = default_ini
    else:
        ini_file_path = input("Please enter the path to the INI file: ")

    # Check if the file exists
    if not os.path.isfile(ini_file_path):
        raise FileNotFoundError(f"The file '{ini_file_path}' does not exist.")

    return ini_file_path


def __get_since_year_input(range_low, range_high, default_year):
    while True:
        try:
            year_input = input(
                f"Please enter a starting year from {range_low} to {range_high} (default is {default_year}): ")
            if year_input.strip() == "":
                return default_year  # Default value
            year = int(year_input)
            if range_low <= year <= range_high:
                return year
            else:
                print(f"Year must be between {range_low} and {range_high}. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a valid year.")


import re


def __is_valid_date(day, month):
    # Check if the month is between 1 and 12
    if month < 1 or month > 12:
        return False
    # Check if the day is valid for the given month
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 1 <= day <= 31
    elif month in [4, 6, 9, 11]:
        return 1 <= day <= 30
    elif month == 2:
        return 1 <= day <= 28  # Assuming February can have up to 28 days for simplicity
    return False


def __get_date_input(prompt, allow_none=False):
    day, month = None, None
    while True:
        user_input = input(prompt)
        if user_input.strip() == "" and allow_none:
            break
        # Check if the input matches the 'dd-mm' format using a regular expression
        match = re.match(r'^(\d{1,2})[-/](\d{1,2})$', user_input.strip())
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            if __is_valid_date(day, month):
                break
            else:
                print("Invalid date. Please enter a valid day and month.")
        else:
            print("Invalid format. Please enter the date in 'dd-mm' format.")
    return day, month


def __get_dates_of_year():
    day1, month1 = __get_date_input("Please enter the starting day for fetching movies 'dd-mm' format: ")

    while True:
        day2, month2 = __get_date_input("Now enter the last day for fetching movies 'dd-mm'"
                                      " format (or nothing if same day as first input): ", True)
        if day2 is None and month2 is None:
            day2 = day1
            month2 = month1
            break
        elif (month2 > month1) or (month2 == month1 and day2 > day1):
            break
        else:
            print("The second date must be later in the year than the first date. Please try again.")
    return datetime(MINYEAR, month1, day1), datetime(MINYEAR, month2, day2)

def __remove_duplicates(json_list):
    seen_ids = set()
    unique_json_list = []

    for item in json_list:
        item_id = item['id']
        if item_id not in seen_ids:
            unique_json_list.append(item)
            seen_ids.add(item_id)

    return unique_json_list

def __filtering(jsons_lst, filtering_mode='most_populars'):
    filtered_jsons_lst = []
    match filtering_mode:
        case 'most_populars':
            flattened_json_lst = [item for item_lst in jsons_lst if item_lst['content'] for item in item_lst['content']]
            filtered_jsons_lst = sorted(flattened_json_lst, key=lambda x: x['popularity'], reverse=True)
        case _:
            raise Exception(f"Unknown filtering mode '{filtering_mode}'")
    return __remove_duplicates(filtered_jsons_lst)

def main():
    try:
        # Read user selected ini file and get global params
        selected_config_file = __get_ini_file()
        selected_config = configparser.ConfigParser()
        selected_config.read(selected_config_file)
        global_params = GlobalConfig(selected_config)

        # Read user starting year date range
        to_year = datetime.now().year
        since_year = __get_since_year_input(1900, to_year, 1900)

        dates_of_year = __get_dates_of_year()
        date_from = dates_of_year[0]
        date_to = dates_of_year[1]
        opts = OptionsDate(since_year, to_year, date_from, date_to)

        # API calls
        client = TmdbDiscoverClient(selected_config, global_params, options_date=opts)
        discovered = __filtering(client.discover_movies())

        print(f"Fetched {len(discovered)} movies")

        # Prepare datas to display
        date_format = '%d %B'
        json_rendered = {'header': f"Movies released between {date_from.strftime(date_format)} "
                                   f"and {date_to.strftime(date_format)} since {since_year}",
                         'content' : discovered}

        # Render it to a nice HTML page
        html_file = html_renderer.render_html_page(json_rendered,
                                                   os.path.join(os.path.dirname(__file__), 'resources', 'templates'),
                                                   'template_lazy.html.jinja',
                                                   os.path.join(os.path.dirname(__file__), 'dist'))

        # Open user browser with generated page
        webbrowser.open('file://' + os.path.realpath(html_file))
    except FileNotFoundError as e:
        print(e)
        print("Please provide a valid INI file.")


if __name__ == "__main__":
    main()
