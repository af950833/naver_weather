"""API wrapper for the Naver Weather integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    AIR_PROVIDER,
    AIR_STATION,
    AIR_UPDATED,
    BRAND,
    BSE_URL,
    CAI_GRADE,
    CO_GRADE,
    CONDITION,
    CONDITIONS,
    CONF_AREA,
    CONF_TODAY,
    DEFAULT_AREA,
    DEVICE_REG,
    DEVICE_UNREG,
    DEVICE_UPDATE,
    FEEL_TEMP,
    LAST_ERROR,
    LAST_SUCCESS,
    LOCATION,
    MAX_TEMP,
    MIN_TEMP,
    MODEL,
    NDUST,
    NDUST_GRADE,
    NO2_GRADE,
    NOW_CAST,
    NOW_HUMI,
    NOW_TEMP,
    NOW_WEATHER,
    OZON_GRADE,
    RAIN_PERCENT,
    RAIN_EXPECTED,
    RAIN_EXPECTED_TMR,
    RAINFALL,
    RAINY_START,
    RAINY_START_TMR,
    SO2_GRADE,
    SUN_TIMES,
    SW_VERSION,
    TOMORROW_AM,
    TOMORROW_MAX,
    TOMORROW_MIN,
    TOMORROW_PM,
    UDUST,
    UDUST_GRADE,
    UV_GRADE,
    WIND_DIR,
    WIND_SPEED,
)

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://www.naver.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.5,en;q=0.3",
}


def re2num(value):
    """Extract the first integer as text."""
    match = re.search(r"-?\d+", value or "")
    return match.group(0) if match else None


def re2float(value):
    """Extract the first decimal number as text."""
    match = re.search(r"-?\d+(?:\.\d+)?", value or "")
    return match.group(0) if match else None


def _to_float(value):
    """Convert a value to float when possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    """Convert a value to int when possible."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _condition_from_icon(icon_class):
    """Convert Naver weather icon class to a Home Assistant condition."""
    if not icon_class:
        return None
    key = icon_class.replace("ico_", "")
    return CONDITIONS.get(key, [None])[0]


HANGUL_INITIALS = (
    "g",
    "kk",
    "n",
    "d",
    "tt",
    "r",
    "m",
    "b",
    "pp",
    "s",
    "ss",
    "",
    "j",
    "jj",
    "ch",
    "k",
    "t",
    "p",
    "h",
)
HANGUL_MEDIALS = (
    "a",
    "ae",
    "ya",
    "yae",
    "eo",
    "e",
    "yeo",
    "ye",
    "o",
    "wa",
    "wae",
    "oe",
    "yo",
    "u",
    "wo",
    "we",
    "wi",
    "yu",
    "eu",
    "ui",
    "i",
)
HANGUL_FINALS = (
    "",
    "k",
    "k",
    "ks",
    "n",
    "nj",
    "nh",
    "t",
    "l",
    "lk",
    "lm",
    "lb",
    "ls",
    "lt",
    "lp",
    "lh",
    "m",
    "p",
    "ps",
    "t",
    "t",
    "ng",
    "t",
    "t",
    "k",
    "t",
    "p",
    "t",
)


def _slugify_korean(value):
    """Return a Home Assistant-friendly ASCII slug while preserving digits."""
    parts = []
    for char in value:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            syllable = code - 0xAC00
            initial = syllable // 588
            medial = (syllable % 588) // 28
            final = syllable % 28
            parts.append(
                HANGUL_INITIALS[initial]
                + HANGUL_MEDIALS[medial]
                + HANGUL_FINALS[final]
            )
        elif char.isascii() and char.isalnum():
            parts.append(char.lower())
        else:
            parts.append("_")

    return re.sub(r"_+", "_", "".join(parts)).strip("_")


class NWeatherAPI:
    """Naver Weather API."""

    def __init__(self, hass, entry, count):
        """Initialize the Naver Weather API."""
        self.hass = hass
        self.entry = entry
        self.count = count
        self.result = {}
        self.forecast = []
        self.available = True
        self.last_error = None
        self.last_success = None
        self.version = SW_VERSION
        self.model = MODEL
        self.brand = BRAND.lower()
        self.brand_name = BRAND
        self.unique = {}

        _LOGGER.debug("[%s] Initialize -> %s", BRAND, self.area)

    @property
    def raw_area(self):
        """Return the configured area."""
        area = self.entry.options.get(
            CONF_AREA, self.entry.data.get(CONF_AREA, DEFAULT_AREA)
        )
        return " ".join((area or DEFAULT_AREA).strip().split()) or DEFAULT_AREA

    @property
    def dong_slug(self):
        """Return the configured dong name as a short ASCII slug."""
        dong = self.raw_area.split()[-1]
        if dong.endswith("동"):
            dong = dong[:-1]
        return _slugify_korean(dong) or "area"

    @property
    def is_default_area(self):
        """Return whether the default Naver weather query is used."""
        return self.raw_area == DEFAULT_AREA

    @property
    def is_dong_area(self):
        """Return whether the configured area is a neighborhood-level query."""
        return self.raw_area.endswith("동")

    @property
    def area(self):
        """Return the Naver search query."""
        if self.is_default_area or self.raw_area.endswith(("날씨", "일기예보")):
            return self.raw_area
        return f"{self.raw_area} 일기예보"

    @property
    def air_area(self):
        """Return the Naver air-quality search query."""
        if self.is_default_area:
            return "미세먼지"
        return f"{self.raw_area} 미세먼지"

    @property
    def today(self):
        """Return whether forecast includes today's weather."""
        return self.entry.options.get(CONF_TODAY, self.entry.data.get(CONF_TODAY, False))

    def init_device(self, unique_id):
        """Initialize device callbacks."""
        self.unique.setdefault(
            unique_id,
            {
                DEVICE_UPDATE: None,
                DEVICE_REG: self.register_update_state,
                DEVICE_UNREG: self.unregister_update_state,
            },
        )

    def get_device(self, unique_id, key):
        """Get device info."""
        return self.unique.get(unique_id, {}).get(key)

    def device_update(self, device_id):
        """Update device state."""
        unique_id = f"{self.raw_area}:{device_id}"
        device_update = self.unique.get(unique_id, {}).get(DEVICE_UPDATE)
        if device_update is not None:
            device_update()

    def register_update_state(self, unique_id, cb):
        """Register device update function to update entity state."""
        device = self.unique.setdefault(unique_id, {})
        if not device.get(DEVICE_UPDATE):
            _LOGGER.info("[%s] Register device => %s [%s]", BRAND, unique_id, self.area)
            device[DEVICE_UPDATE] = cb

    def unregister_update_state(self, unique_id):
        """Unregister device update function."""
        device = self.unique.get(unique_id)
        if device and device.get(DEVICE_UPDATE) is not None:
            _LOGGER.info("[%s] Unregister device => %s [%s]", BRAND, unique_id, self.area)
            device[DEVICE_UPDATE] = None

    def _bs4_select_one(self, soup, selector, bText=True, tag=""):
        """Return a selected BeautifulSoup node or its stripped text."""
        try:
            node = soup.select_one(selector) if soup is not None else None
            if node is None:
                return None
            return node.text.strip() if bText else node
        except Exception as err:
            _LOGGER.debug("[%s] select_one failed (%s): %s", BRAND, tag or selector, err)
            return None

    async def update(self):
        """Update weather information."""
        url = BSE_URL.format(quote_plus(self.area))
        url_air = BSE_URL.format(quote_plus(self.air_area))

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=HEADERS, timeout=30) as response:
                response.raise_for_status()
                soup = BeautifulSoup(await response.text(), "html.parser")

            async with session.get(url_air, headers=HEADERS, timeout=30) as response:
                response.raise_for_status()
                bs4air = BeautifulSoup(await response.text(), "html.parser")

            detail_soup = None
            detail_url = self._parse_weather_detail_url(soup)
            if detail_url:
                try:
                    async with session.get(detail_url, headers=HEADERS, timeout=30) as response:
                        response.raise_for_status()
                        detail_soup = BeautifulSoup(await response.text(), "html.parser")
                except Exception as err:
                    _LOGGER.debug("[%s] Failed to fetch weather detail page: %s", BRAND, err)

            self.last_success = datetime.now().isoformat(timespec="seconds")
            self.last_error = None
            self.result = self._parse_weather(soup, bs4air, detail_soup)
            self.available = True

            _LOGGER.debug("[%s] Updated weather information -> %s", BRAND, self.result)

            self._update_registered_devices()
        except Exception as err:
            self.available = False
            self.last_error = str(err)
            self.result[LAST_ERROR[0]] = self.last_error
            self.result[LAST_SUCCESS[0]] = self.last_success
            self._update_registered_devices()
            _LOGGER.error("[%s] Failed to update Naver Weather: %s", BRAND, err)

    def _update_registered_devices(self):
        """Notify all registered entities that data changed."""
        for unique_id, device in self.unique.items():
            device_update = device.get(DEVICE_UPDATE)
            if device_update is None:
                continue
            try:
                device_update()
            except Exception as err:
                _LOGGER.debug("[%s] Device update failed for %s: %s", BRAND, unique_id, err)

    def _parse_weather(self, soup, bs4air, detail_soup=None):
        """Parse Naver weather and air quality pages."""
        location = self._bs4_select_one(soup, "div.title_area._area_panel > h2.title")
        now_temp = re2float(self._bs4_select_one(soup, "div.temperature_text"))
        now_weather = self._bs4_select_one(soup, "div.temperature_info > p span.weather")
        weather_cast = _remove_trailing_text(self._parse_weather_cast(soup), now_weather)
        min_temp = re2num(self._bs4_select_one(soup, "li.week_item.today span.lowest"))
        max_temp = re2num(self._bs4_select_one(soup, "li.week_item.today span.highest"))
        summary = self._bs4_select_one(soup, "div.temperature_info > dl")

        feel_temp = re2float(_extract_after_label(summary, "체감"))
        humidity = re2num(_extract_after_label(summary, "습도"))
        wind_speed = re2float(_extract_wind(summary))
        wind_dir = _extract_wind_direction(summary)
        rainfall = self._bs4_select_one(soup, "div.climate_box div.graph_wrap ul li div") or "0"
        rain_percent = self._parse_rain_percent(soup)
        uv_grade = self._parse_report_card(soup, "자외선") or "데이터 없음"
        condition = self._parse_condition(soup)
        rainy_start, rainy_start_tmr = self._parse_rain_start(soup)
        rain_expected = rainy_start != "비 안옴"
        rain_expected_tmr = rainy_start_tmr != "비 안옴"
        forecast, tomorrow = self._parse_forecast(soup)
        air = self._parse_air_quality(soup, bs4air)
        air_meta = self._parse_air_metadata(bs4air)
        sun_times = self._parse_sun_times(detail_soup) or self._parse_sun_times(soup) or {}

        self.forecast = forecast

        return {
            LOCATION[0]: location or self.raw_area,
            NOW_CAST[0]: weather_cast,
            NOW_WEATHER[0]: now_weather,
            NOW_TEMP[0]: now_temp,
            NOW_HUMI[0]: humidity,
            CONDITION[0]: condition,
            WIND_SPEED[0]: wind_speed,
            WIND_DIR[0]: wind_dir,
            MIN_TEMP[0]: min_temp,
            MAX_TEMP[0]: max_temp,
            FEEL_TEMP[0]: feel_temp,
            RAINFALL[0]: rainfall,
            UV_GRADE[0]: uv_grade,
            SUN_TIMES[0]: sun_times.get("state"),
            "sunrise": sun_times.get("sunrise"),
            "sunset": sun_times.get("sunset"),
            "next_sun_event": sun_times.get("next_event"),
            "next_sun_event_label": sun_times.get("next_event_label"),
            "next_sun_event_time": sun_times.get("next_event_time"),
            "next_sun_event_datetime": sun_times.get("next_event_datetime"),
            NDUST[0]: air.get(NDUST[0], "0"),
            NDUST_GRADE[0]: air.get(NDUST_GRADE[0]),
            UDUST[0]: air.get(UDUST[0], "0"),
            UDUST_GRADE[0]: air.get(UDUST_GRADE[0]),
            OZON_GRADE[0]: air.get(OZON_GRADE[0]),
            CO_GRADE[0]: air.get(CO_GRADE[0]),
            SO2_GRADE[0]: air.get(SO2_GRADE[0]),
            NO2_GRADE[0]: air.get(NO2_GRADE[0]),
            CAI_GRADE[0]: air.get(CAI_GRADE[0]),
            TOMORROW_AM[0]: tomorrow["am_state"],
            TOMORROW_MIN[0]: tomorrow["min_temp"],
            TOMORROW_PM[0]: tomorrow["pm_state"],
            TOMORROW_MAX[0]: tomorrow["max_temp"],
            RAINY_START[0]: rainy_start,
            RAINY_START_TMR[0]: rainy_start_tmr,
            RAIN_EXPECTED[0]: rain_expected,
            RAIN_EXPECTED_TMR[0]: rain_expected_tmr,
            RAIN_PERCENT[0]: rain_percent,
            AIR_STATION[0]: air_meta["station"],
            AIR_PROVIDER[0]: air_meta["provider"],
            AIR_UPDATED[0]: air_meta["updated"],
            LAST_SUCCESS[0]: self.last_success,
            LAST_ERROR[0]: self.last_error,
        }

    def _parse_weather_detail_url(self, soup):
        """Return the Naver Weather detail page URL from search results."""
        node = None
        if soup is not None:
            for link in soup.select('a[href*="weather.naver.com/today/"]'):
                href = link.get("href", "")
                if "/talk" not in href:
                    node = link
                    break
        if node is None:
            return None
        href = node.get("href")
        if not href:
            return None
        if href.startswith("//"):
            return f"https:{href}"
        if href.startswith("/"):
            return f"https://weather.naver.com{href}"
        return href.split("#", 1)[0]

    def _parse_sun_times(self, soup):
        """Parse sun times and expose the next sunrise/sunset event."""
        if soup is None:
            return None

        text = soup.get_text(" ", strip=True)
        html = str(soup)
        sunrise = None
        sunset = None
        items = []

        match = re.search(r'"sunRiseSetList"\s*:\s*(\[[^\]]+\])', html)
        if match:
            try:
                items = json.loads(match.group(1))
            except json.JSONDecodeError:
                items = []
            today = datetime.now().strftime("%Y%m%d")
            item = next((entry for entry in items if entry.get("aplYmd") == today), items[0] if items else None)
            if item:
                sunrise = _format_hhmm(item.get("sriseTm"))
                sunset = _format_hhmm(item.get("ssetTm"))

        if sunrise is None:
            sunrise = _extract_time_after_label(text, "일출") or _extract_time_after_label(text, "해돋이")
        if sunset is None:
            sunset = _extract_time_after_label(text, "일몰")

        if not items and (sunrise or sunset):
            items = [{
                "aplYmd": datetime.now().strftime("%Y%m%d"),
                "sriseTm": sunrise,
                "ssetTm": sunset,
            }]

        next_event = _next_sun_event(items, datetime.now())
        state = (
            f"{next_event['label']} {next_event['time']}"
            if next_event is not None
            else f"{sunrise} / {sunset}" if sunrise and sunset else sunrise or sunset
        )
        if not state:
            return None
        return {
            "state": state,
            "sunrise": sunrise,
            "sunset": sunset,
            "next_event": next_event["event"] if next_event else None,
            "next_event_label": next_event["label"] if next_event else None,
            "next_event_time": next_event["time"] if next_event else None,
            "next_event_datetime": next_event["datetime"].isoformat(timespec="minutes")
            if next_event
            else None,
        }

    def _parse_weather_cast(self, soup):
        """Parse current weather text."""
        node = self._bs4_select_one(soup, "div.temperature_info > p", False)
        if node is None:
            return None
        return " ".join(node.stripped_strings) or None

    def _parse_condition(self, soup):
        """Parse Home Assistant weather condition."""
        icon = self._bs4_select_one(soup, "div.weather_main > i.wt_icon", False)
        if icon is None:
            return None
        classes = icon.get("class", [])
        icon_class = next((item for item in classes if item.startswith("ico_")), None)
        return _condition_from_icon(icon_class)

    def _parse_report_card(self, soup, label):
        """Parse a value from today's report cards."""
        for item in soup.select("div.report_card_wrap li.item_today"):
            title = self._bs4_select_one(item, "strong.title") or ""
            if label in title:
                return self._bs4_select_one(item, "span.txt")
        return None

    def _parse_rain_percent(self, soup):
        """Return average rain probability for the visible hourly forecast."""
        values = []
        for item in soup.select("div.climate_box div.icon_wrap ul li em")[:12]:
            number = _to_int(re2num(item.text))
            if number is not None:
                values.append(number)
        if not values:
            return "0"
        return str(round(sum(values) / len(values), 1))

    def _parse_rain_start(self, soup):
        """Parse first rainy hour today and tomorrow."""
        today = "비 안옴"
        tomorrow = "비 안옴"
        current_day = "today"

        for item in soup.select("div.graph_inner._hourly_weather dl.graph_content"):
            time = self._bs4_select_one(item, "dt.time") or ""
            weather = self._bs4_select_one(item, "i.wt_icon") or ""

            if "내일" in time:
                current_day = "tomorrow"
            elif "모레" in time:
                current_day = "later"

            is_rain = any(keyword in weather for keyword in ("비", "소나기", "눈"))
            if current_day == "today" and today == "비 안옴" and is_rain:
                today = time
            elif current_day == "tomorrow" and tomorrow == "비 안옴" and is_rain:
                tomorrow = time if "내일" in time else f"내일 {time}"

        return today, tomorrow

    def _parse_forecast(self, soup):
        """Parse weekly forecast."""
        weekly = soup.find("div", {"class": "weekly_forecast_area _toggle_panel"})
        date_info = weekly.find_all("li", {"class": "week_item"}) if weekly else []
        forecast = []
        tomorrow = {
            "min_temp": "-",
            "max_temp": "-",
            "am_state": "-",
            "pm_state": "-",
        }

        reftime = datetime.now()
        started = False

        for item in date_info:
            day_desc = self._bs4_select_one(item, "div.cell_date strong.day") or ""
            if day_desc == "오늘":
                started = True
            if not started and date_info:
                started = True
            if not started:
                continue

            low = _to_float(re2num(self._bs4_select_one(item, "span.lowest")))
            high = _to_float(re2num(self._bs4_select_one(item, "span.highest")))
            condition_icons = item.select("div.cell_weather span i")
            rain_items = item.select("div.cell_weather span.weather_left span.rainfall")
            condition_texts = item.select("div.cell_weather span i.wt_icon span")

            if len(condition_icons) < 2:
                reftime += timedelta(days=1)
                continue

            condition_am = _condition_from_icon(_first_icon_class(condition_icons[0]))
            condition_pm = _condition_from_icon(_first_icon_class(condition_icons[1]))
            if not condition_am or not condition_pm:
                reftime += timedelta(days=1)
                continue
            condition_text_am = (
                condition_texts[0].text.strip()
                if len(condition_texts) > 0
                else condition_am
            )
            condition_text_pm = (
                condition_texts[1].text.strip()
                if len(condition_texts) > 1
                else condition_pm
            )

            data = {
                "datetime": reftime,
                "templow": low,
                "temperature": high,
                "condition": condition_pm,
                "condition_am": condition_am,
                "condition_pm": condition_pm,
                "condition_text_am": condition_text_am,
                "condition_text_pm": condition_text_pm,
                "rain_rate_am": _to_int(re2num(rain_items[0].text))
                if len(rain_items) > 0
                else None,
                "rain_rate_pm": _to_int(re2num(rain_items[1].text))
                if len(rain_items) > 1
                else None,
            }

            if self.today or day_desc != "오늘":
                forecast.append(data)

            if day_desc == "내일":
                tomorrow = {
                    "min_temp": re2num(self._bs4_select_one(item, "span.lowest")) or "-",
                    "max_temp": re2num(self._bs4_select_one(item, "span.highest")) or "-",
                    "am_state": condition_text_am,
                    "pm_state": condition_text_pm,
                }

            reftime += timedelta(days=1)

        return forecast, tomorrow

    def _parse_air_quality(self, weather_soup, dust_soup):
        """Parse air quality data."""
        fine_dust_grade = self._parse_report_card(weather_soup, "미세먼지")
        ultra_fine_dust_grade = self._parse_report_card(weather_soup, "초미세먼지")
        air = {
            NDUST[0]: self._parse_dong_air_value(dust_soup, 1),
            NDUST_GRADE[0]: fine_dust_grade
            or self._parse_legacy_air_grade(dust_soup, 1),
            UDUST[0]: self._parse_dong_air_value(dust_soup, 2),
            UDUST_GRADE[0]: ultra_fine_dust_grade
            or self._parse_legacy_air_grade(dust_soup, 2),
        }

        grade_map = {
            OZON_GRADE[1]: OZON_GRADE[0],
            CO_GRADE[1]: CO_GRADE[0],
            SO2_GRADE[1]: SO2_GRADE[0],
            NO2_GRADE[1]: NO2_GRADE[0],
            CAI_GRADE[1]: CAI_GRADE[0],
        }
        for item in dust_soup.select("div.other_air_info ul.air_info_list > li"):
            title = self._bs4_select_one(item, "span.info_title")
            state = self._bs4_select_one(item, "span.state")
            if title in grade_map:
                air[grade_map[title]] = state

        return air

    def _parse_dong_air_value(self, soup, legacy_index):
        """Parse dong-level PM value from Naver's state_info layout."""
        legacy_value = self._bs4_select_one(
            soup, f"div.state_info:nth-of-type({legacy_index}) span.num"
        )
        return re2num(legacy_value)

    def _parse_legacy_air_grade(self, soup, legacy_index):
        """Parse air-quality grade from Naver's legacy result layout."""
        return self._bs4_select_one(
            soup, f"div.state_info:nth-of-type({legacy_index}) div.grade > span.text"
        )

    def _parse_air_metadata(self, soup):
        """Parse station, provider, and update time for air-quality data."""
        offer = soup.select_one("div.offer_info")
        if offer is None:
            return {"station": None, "provider": None, "updated": None}

        provider = self._bs4_select_one(offer, "a")
        paragraphs = [" ".join(p.stripped_strings) for p in offer.select("p")]
        station = None
        updated = None

        if paragraphs:
            first = paragraphs[0]
            station = first.split(provider or "제공")[0].strip() or None
            if station and station.endswith("측정소"):
                station = station
        for text in paragraphs:
            if re.search(r"\d{2,4}\.\d{1,2}\.\d{1,2}|\d{1,2}\.\d{1,2}", text):
                updated = text.strip()
                break

        return {"station": station, "provider": provider, "updated": updated}


def _extract_after_label(text, label):
    """Extract a numeric value after a Korean label."""
    if not text:
        return None
    match = re.search(rf"{label}\s*(-?\d+(?:\.\d+)?)", text)
    return match.group(1) if match else None


def _remove_trailing_text(text, suffix):
    """Remove a duplicated trailing text fragment."""
    if not text or not suffix:
        return text
    text = text.strip()
    suffix = suffix.strip()
    if text == suffix:
        return None
    if text.endswith(suffix):
        return text[: -len(suffix)].strip() or None
    return text


def _extract_wind(text):
    """Extract wind speed from summary text."""
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*m/s", text)
    return match.group(1) if match else None


def _extract_wind_direction(text):
    """Extract Korean wind direction text."""
    if not text:
        return None
    match = re.search(r"(북동|북서|남동|남서|동|서|남|북)풍?", text)
    return match.group(0) if match else None


def _format_hhmm(value):
    """Format HHMMSS or HHMM text as HH:MM."""
    if not value:
        return None
    digits = re.sub(r"\D", "", str(value))
    if len(digits) < 4:
        return None
    return f"{digits[:2]}:{digits[2:4]}"


def _extract_time_after_label(text, label):
    """Extract a HH:MM time after a Korean label."""
    if not text:
        return None
    match = re.search(rf"{label}\s*:?\s*(\d{{1,2}}:\d{{2}})", text)
    if match:
        return match.group(1).zfill(5)
    match = re.search(rf"{label}\s*:?\s*(\d{{3,4}})", text)
    return _format_hhmm(match.group(1)) if match else None


def _next_sun_event(items, now):
    """Return the next sunrise or sunset event from Naver sun data."""
    events = []
    for item in items or []:
        date_text = item.get("aplYmd") or item.get("aplYmdt")
        if not date_text:
            continue
        date_text = str(date_text)[:8]
        for event, label, key in (
            ("sunrise", "일출", "sriseTm"),
            ("sunset", "일몰", "ssetTm"),
        ):
            time_text = _format_hhmm(item.get(key))
            event_datetime = _sun_event_datetime(date_text, time_text)
            if event_datetime is None or event_datetime <= now:
                continue
            events.append({
                "event": event,
                "label": label,
                "time": time_text,
                "datetime": event_datetime,
            })

    if not events:
        return None
    return min(events, key=lambda event: event["datetime"])


def _sun_event_datetime(date_text, time_text):
    """Build a local datetime for a sun event."""
    if not date_text or not time_text:
        return None
    try:
        return datetime.strptime(f"{date_text} {time_text}", "%Y%m%d %H:%M")
    except ValueError:
        return None


def _first_icon_class(node):
    """Return the first Naver weather icon class on a node."""
    classes = node.get("class", [])
    return next((item for item in classes if item.startswith("ico_")), None)
