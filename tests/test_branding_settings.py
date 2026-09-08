import pytest
from pydantic import ValidationError

from app.models.api import SettingsPatch


def test_branding_settings_are_normalized_and_validated():
    settings = SettingsPatch(application_name="  My Timer  ", accent_color="#A855F7")

    assert settings.application_name == "My Timer"
    assert settings.accent_color == "#A855F7"


@pytest.mark.parametrize("accent", ["A855F7", "#FFF", "purple", "#12345G"])
def test_invalid_accent_colours_are_rejected(accent: str):
    with pytest.raises(ValidationError):
        SettingsPatch(accent_color=accent)


@pytest.mark.parametrize("field", ["application_name", "accent_color"])
def test_branding_settings_cannot_be_cleared_with_null(field: str):
    with pytest.raises(ValidationError):
        SettingsPatch(**{field: None})
