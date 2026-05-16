"""Support for Naver Weather sensors."""
from __future__ import annotations

from homeassistant.helpers.entity import Entity, EntityCategory

from .const import (
    AIR_PROVIDER,
    AIR_STATION,
    AIR_UPDATED,
    CAI_GRADE,
    CO_GRADE,
    DOMAIN,
    NDUST,
    NDUST_GRADE,
    NO2_GRADE,
    OZON_GRADE,
    SO2_GRADE,
    SUN_TIMES,
    LAST_ERROR,
    LAST_SUCCESS,
    LOCATION,
    NOW_CAST,
    NOW_WEATHER,
    UDUST,
    UDUST_GRADE,
    RAIN_EXPECTED,
    RAIN_EXPECTED_TMR,
    RAINY_START,
    RAINY_START_TMR,
    TOMORROW_AM,
    TOMORROW_MAX,
    TOMORROW_MIN,
    TOMORROW_PM,
    WIND_DIR,
    WIND_SPEED,
    WEATHER_INFO,
)
from .nweather_device import NWeatherDevice

FORECAST_SENSOR_COUNT = 7

SUGGESTED_OBJECT_IDS = {
    LOCATION[0]: "location",
    NOW_CAST[0]: "current_summary",
    NOW_WEATHER[0]: "current_condition",
    "NowTemp": "temperature",
    "TodayMinTemp": "today_low_temperature",
    "TodayMaxTemp": "today_high_temperature",
    "TodayFeelTemp": "feels_like_temperature",
    "Humidity": "humidity",
    WIND_SPEED[0]: "wind_speed",
    WIND_DIR[0]: "wind_bearing",
    "Rainfall": "rainfall",
    "TodayUVGrade": "uv_grade",
    SUN_TIMES[0]: "sun_times",
    NDUST[0]: "fine_dust",
    NDUST_GRADE[0]: "fine_dust_grade",
    UDUST[0]: "ultra_fine_dust",
    UDUST_GRADE[0]: "ultra_fine_dust_grade",
    OZON_GRADE[0]: "ozone_grade",
    CO_GRADE[0]: "carbon_monoxide_grade",
    SO2_GRADE[0]: "sulfur_dioxide_grade",
    NO2_GRADE[0]: "nitrogen_dioxide_grade",
    CAI_GRADE[0]: "comprehensive_air_quality_grade",
    TOMORROW_AM[0]: "tomorrow_am_condition",
    TOMORROW_PM[0]: "tomorrow_pm_condition",
    TOMORROW_MIN[0]: "tomorrow_low_temperature",
    TOMORROW_MAX[0]: "tomorrow_high_temperature",
    RAINY_START[0]: "rain_start_time",
    RAINY_START_TMR[0]: "tomorrow_rain_start_time",
    RAIN_EXPECTED[0]: "rain_expected_today",
    RAIN_EXPECTED_TMR[0]: "rain_expected_tomorrow",
    "rainPercent": "rain_probability",
    AIR_STATION[0]: "air_station",
    AIR_PROVIDER[0]: "air_provider",
    AIR_UPDATED[0]: "air_updated",
    LAST_SUCCESS[0]: "last_success",
    LAST_ERROR[0]: "last_error",
}

GRADE_SOURCE_BY_SENSOR = {
    NDUST[0]: NDUST_GRADE[0],
    UDUST[0]: UDUST_GRADE[0],
}

GRADE_ICON_SENSORS = {
    OZON_GRADE[0],
    CO_GRADE[0],
    SO2_GRADE[0],
    NO2_GRADE[0],
    CAI_GRADE[0],
}

GRADE_ICONS = {
    "좋음": "mdi:numeric-1-circle",
    "보통": "mdi:numeric-2-circle",
    "나쁨": "mdi:numeric-3-circle",
    "매우나쁨": "mdi:numeric-4-circle",
    "낮음": "mdi:numeric-1-circle",
    "높음": "mdi:numeric-3-circle",
    "매우높음": "mdi:numeric-4-circle",
    "위험": "mdi:numeric-4-circle",
}

WEATHER_ICON_SENSORS = {
    NOW_WEATHER[0],
    TOMORROW_AM[0],
    TOMORROW_PM[0],
}

WEATHER_TEXT_ICONS = {
    "맑음": "mdi:weather-sunny",
    "구름조금": "mdi:weather-partly-cloudy",
    "구름많음": "mdi:weather-partly-cloudy",
    "흐림": "mdi:weather-cloudy",
    "비 또는 눈": "mdi:weather-snowy-rainy",
    "진눈깨비": "mdi:weather-snowy-rainy",
    "비": "mdi:weather-rainy",
    "한때 비": "mdi:weather-rainy",
    "소나기": "mdi:weather-pouring",
    "눈": "mdi:weather-snowy",
    "안개": "mdi:weather-fog",
    "황사": "mdi:weather-fog",
    "번개": "mdi:weather-lightning",
}

DIAGNOSTIC_SENSORS = {
    AIR_PROVIDER[0],
    AIR_STATION[0],
    AIR_UPDATED[0],
    LAST_ERROR[0],
    LAST_SUCCESS[0],
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Naver Weather sensors."""
    api = hass.data[DOMAIN]["api"][config_entry.entry_id]
    entities = [NWeatherSensor(device, api) for device in WEATHER_INFO.values()]
    entities.extend(
        NWeatherForecastSensor(index, api) for index in range(FORECAST_SENSOR_COUNT)
    )
    async_add_entities(entities)


class NWeatherSensor(NWeatherDevice, Entity):
    """Representation of a Naver Weather sensor."""

    def __init__(self, device, api):
        """Initialize the sensor."""
        super().__init__(device, api)
        suffix = SUGGESTED_OBJECT_IDS.get(self.device[0])
        if suffix is not None:
            self.entity_id = f"sensor.naver_weather_{self.api.dong_slug}_{suffix}"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.device[0] == LAST_ERROR[0]:
            return self.api.result.get(self.device[0]) or "없음"
        if self.device[0] in (RAIN_EXPECTED[0], RAIN_EXPECTED_TMR[0]):
            return "있음" if self.api.result.get(self.device[0]) else "없음"
        return _coerce_number(self.api.result.get(self.device[0]))

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.device[1]

    @property
    def suggested_object_id(self):
        """Return a clean English object id for Home Assistant."""
        suffix = SUGGESTED_OBJECT_IDS.get(self.device[0])
        if suffix is None:
            return None
        return f"naver_weather_{self.api.dong_slug}_{suffix}"

    @property
    def entity_registry_enabled_default(self):
        """Return whether this sensor is enabled by default."""
        return True

    @property
    def icon(self):
        """Return the icon of the sensor."""
        grade_icon = self._numeric_grade_icon
        if grade_icon is not None:
            return grade_icon
        grade_icon = self._grade_icon
        if grade_icon is not None:
            return grade_icon
        weather_icon = self._weather_icon
        if weather_icon is not None:
            return weather_icon
        return self.device[3] or None

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self.device[4] or None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor."""
        return self.device[2] or None

    @property
    def entity_category(self):
        """Return the entity category for diagnostic sensors."""
        if self.device[0] in DIAGNOSTIC_SENSORS:
            return EntityCategory.DIAGNOSTIC
        return None

    @property
    def extra_state_attributes(self):
        """Return extra attributes for automation-friendly sensors."""
        attrs = super().extra_state_attributes
        if self.device[0] == RAINY_START[0]:
            attrs["rain_expected"] = self.api.result.get(RAIN_EXPECTED[0])
        elif self.device[0] == RAINY_START_TMR[0]:
            attrs["rain_expected"] = self.api.result.get(RAIN_EXPECTED_TMR[0])
        elif self.device[0] in (NDUST[0], UDUST[0]):
            attrs["grade"] = self.api.result.get(GRADE_SOURCE_BY_SENSOR[self.device[0]])
        elif self.device[0] == SUN_TIMES[0]:
            attrs["sunrise"] = self.api.result.get("sunrise")
            attrs["sunset"] = self.api.result.get("sunset")
            attrs["next_event"] = self.api.result.get("next_sun_event")
            attrs["next_event_label"] = self.api.result.get("next_sun_event_label")
            attrs["next_event_time"] = self.api.result.get("next_sun_event_time")
            attrs["next_event_datetime"] = self.api.result.get("next_sun_event_datetime")
        elif self.device[0] in GRADE_ICON_SENSORS:
            attrs["grade_icon"] = self._grade_icon
        return attrs

    @property
    def _numeric_grade_icon(self):
        """Return a numeric grade icon for air-quality value sensors."""
        grade_key = GRADE_SOURCE_BY_SENSOR.get(self.device[0])
        if grade_key is None:
            return None

        value = self.api.result.get(grade_key)
        if not isinstance(value, str):
            return None

        normalized = value.replace(" ", "")
        return GRADE_ICONS.get(normalized)

    @property
    def _weather_icon(self):
        """Return a weather icon for weather text sensors."""
        if self.device[0] not in WEATHER_ICON_SENSORS:
            return None

        value = self.api.result.get(self.device[0])
        if not isinstance(value, str):
            return None

        return _weather_icon_from_text(value)

    @property
    def _grade_icon(self):
        """Return a numeric icon for selected grade sensors."""
        if self.device[0] not in GRADE_ICON_SENSORS:
            return None

        value = self.api.result.get(self.device[0])
        if not isinstance(value, str):
            return None

        normalized = value.replace(" ", "")
        return GRADE_ICONS.get(normalized)


def _coerce_number(value):
    """Return ints/floats as numbers and all other values unchanged."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, str):
        return value

    value = value.strip()
    if not value:
        return None

    try:
        number = float(value)
    except ValueError:
        return value

    return int(number) if number.is_integer() else number


class NWeatherForecastSensor(NWeatherDevice, Entity):
    """Representation of a Naver Weather weekly forecast sensor."""

    def __init__(self, index, api):
        """Initialize the forecast sensor."""
        self.index = index
        device = [
            f"WeeklyForecast{index + 1}",
            f"주간예보 {index + 1}일",
            "",
            "mdi:calendar-range",
            "",
        ]
        super().__init__(device, api)
        self.entity_id = (
            f"sensor.naver_weather_{self.api.dong_slug}_weekly_forecast_{index + 1}"
        )

    @property
    def state(self):
        """Return the representative forecast condition text."""
        forecast = self._forecast
        if forecast is None:
            return None
        return _condition_daily_text(forecast)

    @property
    def name(self) -> str:
        """Return the name of the forecast sensor."""
        forecast = self._forecast
        if forecast is None:
            return self.device[1]

        forecast_date = forecast.get("datetime")
        if forecast_date is None:
            return self.device[1]
        return f"주간예보 {forecast_date.strftime('%m-%d')}"

    @property
    def suggested_object_id(self):
        """Return a clean English object id for Home Assistant."""
        return (
            f"naver_weather_{self.api.dong_slug}_weekly_forecast_{self.index + 1}"
        )

    @property
    def icon(self):
        """Return the icon for the forecast condition."""
        forecast = self._forecast
        if forecast is None:
            return self.device[3]
        condition = _condition_daily(
            forecast.get("condition_am"),
            forecast.get("condition_pm"),
        )
        return _weather_icon_from_condition(condition) or self.device[3]

    @property
    def extra_state_attributes(self):
        """Return forecast details as attributes."""
        attrs = super().extra_state_attributes
        forecast = self._forecast
        if forecast is None:
            return attrs

        forecast_date = forecast.get("datetime")
        attrs.update(
            {
                "date": forecast_date.date().isoformat()
                if forecast_date is not None
                else None,
                "condition_am": forecast.get("condition_am"),
                "condition_pm": forecast.get("condition_pm"),
                "condition_text_am": forecast.get("condition_text_am"),
                "condition_text_pm": forecast.get("condition_text_pm"),
                "temperature_low": forecast.get("templow"),
                "temperature_high": forecast.get("temperature"),
                "rain_rate_am": forecast.get("rain_rate_am"),
                "rain_rate_pm": forecast.get("rain_rate_pm"),
            }
        )
        return attrs

    @property
    def _forecast(self):
        """Return the forecast payload for this sensor index."""
        forecast = getattr(self.api, "forecast", [])
        if self.index >= len(forecast):
            return None
        return forecast[self.index]


FORECAST_ICONS = {
    "sunny": "mdi:weather-sunny",
    "clear-night": "mdi:weather-night",
    "partlycloudy": "mdi:weather-partly-cloudy",
    "cloudy": "mdi:weather-cloudy",
    "rainy": "mdi:weather-rainy",
    "pouring": "mdi:weather-pouring",
    "snowy": "mdi:weather-snowy",
    "snowy-rainy": "mdi:weather-snowy-rainy",
    "fog": "mdi:weather-fog",
    "lightning": "mdi:weather-lightning",
    "windy": "mdi:weather-windy",
}


def _weather_icon_from_condition(condition):
    """Return an icon from a Home Assistant weather condition."""
    return FORECAST_ICONS.get(condition)


def _weather_icon_from_text(value):
    """Return an icon from Korean weather text."""
    normalized = value.strip()
    if not normalized:
        return None

    for keyword, icon in WEATHER_TEXT_ICONS.items():
        if keyword in normalized:
            return icon
    return None


def _condition_daily(am, pm):
    """Prefer the more severe condition when combining AM/PM forecasts."""
    if not am:
        return pm
    if not pm:
        return am

    for condition in ("snowy", "pouring", "rainy", "cloudy", "windy"):
        if condition in am:
            return am
        if condition in pm:
            return pm
    return am


def _condition_daily_text(forecast):
    """Return the Korean text for the representative daily condition."""
    condition = _condition_daily(
        forecast.get("condition_am"),
        forecast.get("condition_pm"),
    )
    if condition == forecast.get("condition_pm"):
        return forecast.get("condition_text_pm") or condition
    return forecast.get("condition_text_am") or condition
