"""RTSP URL construction tests."""

import pytest

from analytics_vms.inventory import InventoryRow
from analytics_vms.rtsp import RtspUrlError, build_rtsp_url, mask_rtsp_url


def make_row(
    *,
    rtsp_path: str = "/Streaming/Channels/101",
    username: str = "",
    password: str = "",
) -> InventoryRow:
    """Create a normalized inventory row for RTSP tests."""
    return InventoryRow(
        project_code="DEMO01",
        municipality="Sample Municipality",
        site_type="PMI",
        site_code="SITE001",
        site_name="DEMO-PMI-SITE001",
        traffic_direction="",
        camera_role="PTZ",
        camera_name="DEMO-PMI-SITE001-PTZ",
        brand="unknown",
        ip="192.0.2.10",
        rtsp_port=554,
        rtsp_path=rtsp_path,
        transport="tcp",
        username=username,
        password=password,
    )


def test_build_rtsp_url_without_credentials() -> None:
    url = build_rtsp_url(make_row())

    assert url == "rtsp://192.0.2.10:554/Streaming/Channels/101"


def test_build_rtsp_url_with_username_and_password() -> None:
    url = build_rtsp_url(make_row(username="demo-user", password="demo-pass"))

    assert url == "rtsp://demo-user:demo-pass@192.0.2.10:554/Streaming/Channels/101"


def test_build_rtsp_url_escapes_special_credential_characters() -> None:
    password = "p@ss:word/with#space value"
    url = build_rtsp_url(make_row(username="demo user", password=password))

    assert (
        url
        == "rtsp://demo%20user:p%40ss%3Aword%2Fwith%23space%20value"
        "@192.0.2.10:554/Streaming/Channels/101"
    )
    assert password not in mask_rtsp_url(url)


def test_build_rtsp_url_normalizes_path_without_initial_slash() -> None:
    url = build_rtsp_url(make_row(rtsp_path="Streaming/Channels/101"))

    assert url == "rtsp://192.0.2.10:554/Streaming/Channels/101"


def test_build_rtsp_url_keeps_path_with_initial_slash() -> None:
    url = build_rtsp_url(make_row(rtsp_path="/Streaming/Channels/101"))

    assert url == "rtsp://192.0.2.10:554/Streaming/Channels/101"


def test_build_rtsp_url_fails_with_empty_path() -> None:
    with pytest.raises(RtspUrlError) as exc_info:
        build_rtsp_url(make_row(rtsp_path="  "))

    assert "rtsp_path" in str(exc_info.value)


def test_build_rtsp_url_fails_with_incomplete_credentials() -> None:
    with pytest.raises(RtspUrlError) as exc_info:
        build_rtsp_url(make_row(username="demo-user", password=""))

    assert "credenciales incompletas" in str(exc_info.value)


def test_mask_rtsp_url_hides_password() -> None:
    password = "demo-pass"
    url = f"rtsp://admin:{password}@192.0.2.10:554/Streaming/Channels/101"

    masked_url = mask_rtsp_url(url)

    assert masked_url == "rtsp://admin:***@192.0.2.10:554/Streaming/Channels/101"
    assert password not in masked_url


def test_mask_rtsp_url_keeps_url_without_credentials() -> None:
    url = "rtsp://192.0.2.10:554/Streaming/Channels/101"

    assert mask_rtsp_url(url) == url
