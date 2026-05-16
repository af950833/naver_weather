"""Config flow for Naver Weather."""
import re

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_AREA, CONF_TODAY, DEFAULT_AREA, DOMAIN, NW_OPTIONS


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Naver Weather."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            area = _normalize_area(user_input.get(CONF_AREA))
            if not _is_gu_dong_area(area):
                errors[CONF_AREA] = "dong_required"
            else:
                data = {**user_input, CONF_AREA: area}
                await self.async_set_unique_id(area)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=area, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_AREA, default=DEFAULT_AREA): cv.string,
                    vol.Optional(CONF_TODAY, default=False): cv.boolean,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, user_input=None):
        """Handle configuration by YAML file."""
        area = _normalize_area(user_input.get(CONF_AREA))
        if not _is_gu_dong_area(area):
            return self.async_abort(reason="dong_required")
        data = {**user_input, CONF_AREA: area}
        await self.async_set_unique_id(area)
        self._abort_if_unique_id_configured(updates=data)
        return self.async_create_entry(title=area, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle an options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Naver Weather."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        conf = self._config_entry
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema=None)
        if user_input is not None:
            data = {**user_input, CONF_AREA: _normalize_area(user_input.get(CONF_AREA))}
            if not _is_gu_dong_area(data[CONF_AREA]):
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._options_schema(),
                    errors={CONF_AREA: "dong_required"},
                )
            return self.async_create_entry(title="", data=data)

        return self.async_show_form(step_id="init", data_schema=self._options_schema())

    def _options_schema(self):
        """Return the options form schema."""
        options_schema = {}
        for name, default, validation in NW_OPTIONS:
            conf = self._config_entry
            to_default = conf.options.get(name, conf.data.get(name, default))
            key = vol.Optional(name, default=to_default)
            options_schema[key] = validation
        return vol.Schema(options_schema)


def _normalize_area(area: str | None) -> str:
    """Normalize user-provided search area."""
    if not area:
        return DEFAULT_AREA
    return " ".join(area.strip().split()) or DEFAULT_AREA


def _is_gu_dong_area(area: str) -> bool:
    """Return True when area is provided as district and dong."""
    return re.fullmatch(r"\S+구\s+\S+동", area) is not None
