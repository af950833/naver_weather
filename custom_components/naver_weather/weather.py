"""Support for Naver Weather."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import UnitOfSpeed, UnitOfTemperature

from .const import (
    CONDITION,
    DOMAIN,
    NOW_HUMI,
    NOW_TEMP,
    WIND_DIR,
    WIND_SPEED,
)
from .nweather_device import NWeatherDevice

SCAN_INTERVAL = timedelta(minutes=10)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add a weather entity from a config entry."""
    api = hass.data[DOMAIN]["api"][config_entry.entry_id]
    async_add_entities([NWeatherMain(["Naver Weather", "네이버 날씨", "", ""], api)])


class NWeatherMain(NWeatherDevice, WeatherEntity):
    """Representation of Naver Weather conditions."""

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY
        | WeatherEntityFeature.FORECAST_TWICE_DAILY
    )

    def __init__(self, device, api):
        """Initialize the weather entity."""
        super().__init__(device, api)
        self.entity_id = f"weather.naver_weather_{self.api.dong_slug}"

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self.api.raw_area or self.device[1]

    @property
    def suggested_object_id(self):
        """Return a clean English object id for Home Assistant."""
        return f"naver_weather_{self.api.dong_slug}"

    @property
    def native_temperature(self):
        """Return the temperature."""
        return _as_float(self.api.result.get(NOW_TEMP[0]))

    @property
    def humidity(self):
        """Return the humidity."""
        return _as_int(self.api.result.get(NOW_HUMI[0]))

    @property
    def native_wind_speed(self):
        """Return the wind speed in km/h."""
        wind_speed = _as_float(self.api.result.get(WIND_SPEED[0]))
        if wind_speed is None:
            return None
        return round(wind_speed * 3.6, 2)

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        return self.api.result.get(WIND_DIR[0])

    @property
    def condition(self):
        """Return the weather condition."""
        return self.api.result.get(CONDITION[0])

    @property
    def state(self):
        """Return the weather state."""
        return self.condition

    @property
    def attribution(self):
        """Return the attribution."""
        return "Naver Weather"

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return self._forecast(WeatherEntityFeature.FORECAST_DAILY)

    async def async_forecast_twice_daily(self) -> list[Forecast] | None:
        """Return the twice-daily forecast in native units."""
        return self._forecast(WeatherEntityFeature.FORECAST_TWICE_DAILY)

    @property
    def should_poll(self) -> bool:
        """Poll this entity on Home Assistant's weather interval."""
        return True

    async def async_update(self):
        """Update current conditions."""
        await self.api.update()

    @property
    def forecast(self) -> list[Forecast] | None:
        """Return the daily forecast for older Home Assistant versions."""
        return self._forecast(WeatherEntityFeature.FORECAST_DAILY)

    def _forecast(self, feature) -> list[Forecast] | None:
        """Build a forecast payload for Home Assistant."""
        forecast = []

        for data in getattr(self.api, "forecast", []):
            condition_am = data.get("condition_am")
            condition_pm = data.get("condition_pm")
            if not data.get("datetime") or not condition_am or not condition_pm:
                continue

            day = {
                ATTR_FORECAST_TIME: data["datetime"],
                ATTR_FORECAST_CONDITION: self._condition_daily(condition_am, condition_pm),
                ATTR_FORECAST_TEMP_LOW: data.get("templow"),
                ATTR_FORECAST_TEMP: data.get("temperature"),
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: data.get("rain_rate_am"),
                "condition_am": condition_am,
                "condition_pm": condition_pm,
                "rain_rate_am": data.get("rain_rate_am"),
                "rain_rate_pm": data.get("rain_rate_pm"),
            }

            if feature == WeatherEntityFeature.FORECAST_TWICE_DAILY:
                day[ATTR_FORECAST_CONDITION] = condition_am
                day["is_daytime"] = True

            forecast.append(day)

            if feature == WeatherEntityFeature.FORECAST_TWICE_DAILY:
                forecast.append(
                    {
                        ATTR_FORECAST_TIME: data["datetime"],
                        ATTR_FORECAST_CONDITION: condition_pm,
                        ATTR_FORECAST_TEMP_LOW: data.get("templow"),
                        ATTR_FORECAST_TEMP: data.get("temperature"),
                        ATTR_FORECAST_PRECIPITATION_PROBABILITY: data.get("rain_rate_pm"),
                        "is_daytime": False,
                        "condition_am": condition_am,
                        "condition_pm": condition_pm,
                        "rain_rate_am": data.get("rain_rate_am"),
                        "rain_rate_pm": data.get("rain_rate_pm"),
                    }
                )

        return forecast or None

    def _condition_daily(self, am, pm):
        """Prefer the more severe condition when combining AM/PM forecasts."""
        for condition in ("snowy", "pouring", "rainy", "cloudy", "windy"):
            if condition in am:
                return am
            if condition in pm:
                return pm
        return am


def _as_float(value):
    """Return value as float when possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value):
    """Return value as int when possible."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
