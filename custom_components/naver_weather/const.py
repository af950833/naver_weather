"""Constants for Naver Weather."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)

DOMAIN = "naver_weather"
BRAND = "Naver Weather"
MODEL = "NWeather"
PLATFORMS = ["weather", "sensor"]

DEVICE_STATE = "state"
DEVICE_UPDATE = "update"
DEVICE_REG = "register"
DEVICE_UNREG = "unregister"

SW_VERSION = "2.5.5"
BSE_URL = "https://search.naver.com/search.naver?query={}"

CONF_AREA = "area"
CONF_TODAY = "today"
CONF_REGION = "region"
DEFAULT_AREA = ""

OPT_SCAN_INT = "scan_interval"
DEFAULT_SCAN_INT = 15


def int_between(min_int, max_int):
    """Return an integer between min_int and max_int."""
    return vol.All(vol.Coerce(int), vol.Range(min=min_int, max=max_int))


NW_OPTIONS = [
    (CONF_AREA, DEFAULT_AREA, cv.string),
    (CONF_TODAY, False, cv.boolean),
]


CONDITIONS = {
    "wt1": ["sunny", "맑음", "맑음"],
    "wt2": ["clear-night", "맑음", "맑음"],
    "wt3": ["partlycloudy", "구름조금", "구름조금"],
    "wt4": ["partlycloudy", "구름조금", "구름조금"],
    "wt5": ["partlycloudy", "구름많음", "구름많음"],
    "wt6": ["partlycloudy", "구름많음", "구름많음"],
    "wt7": ["cloudy", "흐림", "흐림"],
    "wt8": ["rainy", "비", "강한비"],
    "wt9": ["rainy", "비", "비"],
    "wt10": ["pouring", "소나기", "강한비"],
    "wt11": ["snowy", "눈", "강한눈"],
    "wt12": ["snowy", "눈", "눈"],
    "wt13": ["snowy", "눈", "강한눈"],
    "wt14": ["snowy", "진눈깨비", "진눈깨비"],
    "wt15": ["rainy", "비", "소나기"],
    "wt16": ["snowy-rainy", "진눈깨비", "소낙눈"],
    "wt17": ["fog", "안개", "안개"],
    "wt18": ["lightning", "번개", "번개"],
    "wt19": ["snowy", "눈", "눈보라"],
    "wt20": ["fog", "안개", "황사"],
    "wt21": ["snowy-rainy", "진눈깨비", "비 또는 눈"],
    "wt22": ["rainy", "비", "가끔 비"],
    "wt23": ["snowy", "눈", "가끔 눈"],
    "wt24": ["snowy-rainy", "진눈깨비", "가끔 비 또는 눈"],
    "wt25": ["partlycloudy", "구름조금", "구름 사이 햇살"],
    "wt26": ["partlycloudy", "구름많음", "흐린 후 갬"],
    "wt27": ["partlycloudy", "구름많음", "비 후 갬"],
    "wt28": ["partlycloudy", "구름많음", "눈 후 갬"],
    "wt29": ["rainy", "비", "흩뿌리는 비"],
    "wt30": ["snowy", "눈", "흩뿌리는 눈"],
    "wt31": ["rainy", "비", "가끔 비"],
    "wt32": ["snowy", "눈", "가끔 눈"],
    "wt33": ["snowy-rainy", "진눈깨비", "가끔 비 또는 눈"],
    "wt34": ["partlycloudy", "구름조금", "구름 사이 햇살"],
    "wt35": ["partlycloudy", "구름많음", "흐린 후 갬"],
    "wt36": ["partlycloudy", "구름많음", "비 후 갬"],
    "wt37": ["partlycloudy", "구름많음", "눈 후 갬"],
    "wt38": ["rainy", "비", "흩뿌리는 비"],
    "wt39": ["snowy", "눈", "흩뿌리는 눈"],
    "wt40": ["fog", "안개", "안개"],
    "wt41": ["fog", "안개", "황사"],
}

LOCATION = ["LocationInfo", "위치", "", "mdi:map-marker-radius", ""]
CONDITION = ["Condition", "날씨", "", "", ""]
NOW_CAST = ["WeatherCast", "현재 날씨 정보", "", "mdi:weather-cloudy", ""]
NOW_WEATHER = ["NowWeather", "현재 날씨", "", "mdi:weather-cloudy", ""]

NOW_TEMP = ["NowTemp", "현재 온도", UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorDeviceClass.TEMPERATURE]
MIN_TEMP = ["TodayMinTemp", "오늘 최저 온도", UnitOfTemperature.CELSIUS, "mdi:thermometer-chevron-down", SensorDeviceClass.TEMPERATURE]
MAX_TEMP = ["TodayMaxTemp", "오늘 최고 온도", UnitOfTemperature.CELSIUS, "mdi:thermometer-chevron-up", SensorDeviceClass.TEMPERATURE]
FEEL_TEMP = ["TodayFeelTemp", "체감 온도", UnitOfTemperature.CELSIUS, "mdi:thermometer", SensorDeviceClass.TEMPERATURE]

NOW_HUMI = ["Humidity", "현재 습도", PERCENTAGE, "mdi:water-percent", SensorDeviceClass.HUMIDITY]

WIND_SPEED = ["WindSpeed", "현재 풍속", UnitOfSpeed.METERS_PER_SECOND, "mdi:weather-windy", ""]
WIND_DIR = ["WindBearing", "현재 풍향", "", "mdi:windsock", ""]

RAINFALL = ["Rainfall", "시간당 강수량", UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR, "mdi:weather-pouring", ""]

UV_GRADE = ["TodayUVGrade", "자외선 등급", "", "mdi:weather-sunny-alert", ""]
SUN_TIMES = ["SunTimes", "일출/일몰", "", "mdi:weather-sunset", ""]

UDUST = ["UltraFineDust", "초미세먼지", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, "mdi:blur-linear", SensorDeviceClass.PM25]
NDUST = ["FineDust", "미세먼지", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, "mdi:blur", SensorDeviceClass.PM10]
UDUST_GRADE = ["UltraFineDustGrade", "초미세먼지 등급", "", "mdi:blur-linear", ""]
NDUST_GRADE = ["FineDustGrade", "미세먼지 등급", "", "mdi:blur", ""]

OZON_GRADE = ["OzonGrade", "오존", "", "mdi:alpha-o-circle", ""]
CO_GRADE = ["coGrade", "일산화탄소", "", "mdi:molecule-co", ""]
SO2_GRADE = ["so2Grade", "아황산가스", "", "mdi:alpha-s-circle", ""]
NO2_GRADE = ["no2Grade", "이산화질소", "", "mdi:alpha-n-circle", ""]
CAI_GRADE = ["caiGrade", "통합대기", "", "mdi:alpha-c-circle", ""]

TOMORROW_AM = ["tomorrowMState", "내일 오전 날씨", "", "mdi:weather-cloudy", ""]
TOMORROW_PM = ["tomorrowAState", "내일 오후 날씨", "", "mdi:weather-cloudy", ""]
TOMORROW_MAX = ["tomorrowATemp", "내일 최고 온도", UnitOfTemperature.CELSIUS, "mdi:thermometer-chevron-up", SensorDeviceClass.TEMPERATURE]
TOMORROW_MIN = ["tomorrowMTemp", "내일 최저 온도", UnitOfTemperature.CELSIUS, "mdi:thermometer-chevron-down", SensorDeviceClass.TEMPERATURE]

RAINY_START = ["rainyStart", "비 시작 예상 시간", "", "mdi:weather-rainy", ""]
RAINY_START_TMR = ["rainyStartTmr", "내일 비 시작 예상 시간", "", "mdi:weather-rainy", ""]
RAIN_EXPECTED = ["rainExpectedToday", "오늘 비 예보", "", "mdi:weather-rainy", ""]
RAIN_EXPECTED_TMR = ["rainExpectedTomorrow", "내일 비 예보", "", "mdi:weather-rainy", ""]

RAIN_PERCENT = ["rainPercent", "강수 확률", "%", "mdi:weather-rainy", ""]

AIR_STATION = ["airStation", "대기질 측정소", "", "mdi:map-marker", ""]
AIR_PROVIDER = ["airProvider", "대기질 제공처", "", "mdi:database", ""]
AIR_UPDATED = ["airUpdated", "대기질 업데이트 시간", "", "mdi:clock-outline", ""]
LAST_SUCCESS = ["lastSuccess", "마지막 업데이트 성공", "", "mdi:check-circle-outline", ""]
LAST_ERROR = ["lastError", "마지막 업데이트 오류", "", "mdi:alert-circle-outline", ""]

WEATHER_INFO = {
    LOCATION[0]: LOCATION,
    NOW_CAST[0]: NOW_CAST,
    NOW_TEMP[0]: NOW_TEMP,
    MIN_TEMP[0]: MIN_TEMP,
    MAX_TEMP[0]: MAX_TEMP,
    FEEL_TEMP[0]: FEEL_TEMP,
    NOW_HUMI[0]: NOW_HUMI,
    WIND_SPEED[0]: WIND_SPEED,
    WIND_DIR[0]: WIND_DIR,
    RAINFALL[0]: RAINFALL,
    UV_GRADE[0]: UV_GRADE,
    SUN_TIMES[0]: SUN_TIMES,
    UDUST[0]: UDUST,
    NDUST[0]: NDUST,
    UDUST_GRADE[0]: UDUST_GRADE,
    NDUST_GRADE[0]: NDUST_GRADE,
    OZON_GRADE[0]: OZON_GRADE,
    CO_GRADE[0]: CO_GRADE,
    SO2_GRADE[0]: SO2_GRADE,
    NO2_GRADE[0]: NO2_GRADE,
    CAI_GRADE[0]: CAI_GRADE,
    TOMORROW_PM[0]: TOMORROW_PM,
    TOMORROW_MAX[0]: TOMORROW_MAX,
    TOMORROW_AM[0]: TOMORROW_AM,
    TOMORROW_MIN[0]: TOMORROW_MIN,
    RAINY_START[0]: RAINY_START,
    RAINY_START_TMR[0]: RAINY_START_TMR,
    RAIN_EXPECTED[0]: RAIN_EXPECTED,
    RAIN_EXPECTED_TMR[0]: RAIN_EXPECTED_TMR,
    RAIN_PERCENT[0]: RAIN_PERCENT,
    NOW_WEATHER[0]: NOW_WEATHER,
    AIR_STATION[0]: AIR_STATION,
    AIR_PROVIDER[0]: AIR_PROVIDER,
    AIR_UPDATED[0]: AIR_UPDATED,
    LAST_SUCCESS[0]: LAST_SUCCESS,
    LAST_ERROR[0]: LAST_ERROR,
}
