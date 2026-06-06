from day1.tools.fetch_url import fetch_url
from day1.tools.location import get_current_location
from day1.tools.time_tool import get_current_datetime
from day1.tools.weather import get_weather
from day1.tools.web_tool import web_search

TOOLS = [get_weather, web_search, fetch_url, get_current_location, get_current_datetime]


def get_tools():
    return TOOLS
