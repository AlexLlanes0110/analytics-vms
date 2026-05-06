"""ffmpeg frame validation tests."""

from __future__ import annotations

import subprocess
from typing import Any

from analytics_vms.frames import FrameValidationResult, validate_rtsp_frames


RTSP_URL = "rtsp://192.0.2.10:554/Streaming/Channels/101"


def _mock_subprocess_run(
    monkeypatch: Any,
    *,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
    expected_min_frames: int = 1,
) -> None:
    """Mock subprocess.run with a CompletedProcess response."""

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert args == [
            "ffmpeg",
            "-v",
            "error",
            "-rtsp_transport",
            "tcp",
            "-i",
            RTSP_URL,
            "-frames:v",
            str(expected_min_frames),
            "-f",
            "null",
            "-",
        ]
        assert isinstance(args, list)
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is False
        assert "shell" not in kwargs
        return subprocess.CompletedProcess(
            args=args,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr("analytics_vms.frames.subprocess.run", fake_run)


def test_validate_rtsp_frames_success(monkeypatch: Any) -> None:
    _mock_subprocess_run(monkeypatch, returncode=0, expected_min_frames=1)

    result = validate_rtsp_frames(RTSP_URL, timeout_seconds=2)

    assert result == FrameValidationResult(
        frames_ok=1,
        ok=True,
        timed_out=False,
        returncode=0,
        error="",
        raw_stdout="",
        raw_stderr="",
        decoded_frames=1,
    )


def test_validate_rtsp_frames_nonzero_returncode(monkeypatch: Any) -> None:
    _mock_subprocess_run(
        monkeypatch,
        returncode=1,
        stderr="could not decode frames",
    )

    result = validate_rtsp_frames(RTSP_URL, timeout_seconds=2)

    assert result.frames_ok == 0
    assert result.ok is False
    assert result.returncode == 1
    assert result.decoded_frames == 0
    assert "return code 1" in result.error


def test_validate_rtsp_frames_timeout(monkeypatch: Any) -> None:
    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=args,
            timeout=kwargs["timeout"],
            output="partial stdout",
            stderr="partial stderr",
        )

    monkeypatch.setattr("analytics_vms.frames.subprocess.run", fake_run)

    result = validate_rtsp_frames(RTSP_URL, timeout_seconds=2)

    assert result.frames_ok == 0
    assert result.ok is False
    assert result.timed_out is True
    assert result.returncode is None
    assert result.decoded_frames == 0
    assert "timed out" in result.error


def test_validate_rtsp_frames_file_not_found(monkeypatch: Any) -> None:
    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError

    monkeypatch.setattr("analytics_vms.frames.subprocess.run", fake_run)

    result = validate_rtsp_frames(RTSP_URL, timeout_seconds=2)

    assert result.frames_ok == 0
    assert result.ok is False
    assert result.returncode is None
    assert result.error == "ffmpeg executable not found."


def test_validate_rtsp_frames_masks_password_in_outputs(monkeypatch: Any) -> None:
    password = "demo-secret"
    url = f"rtsp://admin:{password}@192.0.2.10:554/Streaming/Channels/101"

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout=f"stdout mentions {url}",
            stderr=f"stderr mentions {url} and {password}",
        )

    monkeypatch.setattr("analytics_vms.frames.subprocess.run", fake_run)

    result = validate_rtsp_frames(url, timeout_seconds=2)

    assert result.frames_ok == 0
    assert password not in result.error
    assert password not in result.raw_stdout
    assert password not in result.raw_stderr
    assert "rtsp://admin:***@192.0.2.10:554/Streaming/Channels/101" in result.raw_stdout


def test_validate_rtsp_frames_masks_encoded_and_decoded_password_tokens(
    monkeypatch: Any,
) -> None:
    encoded_password = "demo%20secret"
    decoded_password = "demo secret"
    url = f"rtsp://admin:{encoded_password}@192.0.2.10:554/Streaming/Channels/101"

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout=f"stdout mentions {url}",
            stderr=f"stderr mentions decoded token {decoded_password}",
        )

    monkeypatch.setattr("analytics_vms.frames.subprocess.run", fake_run)

    result = validate_rtsp_frames(url, timeout_seconds=2)

    assert result.frames_ok == 0
    assert encoded_password not in result.error
    assert encoded_password not in result.raw_stdout
    assert encoded_password not in result.raw_stderr
    assert decoded_password not in result.error
    assert decoded_password not in result.raw_stdout
    assert decoded_password not in result.raw_stderr


def test_validate_rtsp_frames_passes_min_frames_to_command(monkeypatch: Any) -> None:
    _mock_subprocess_run(monkeypatch, returncode=0, expected_min_frames=3)

    result = validate_rtsp_frames(RTSP_URL, timeout_seconds=2, min_frames=3)

    assert result.frames_ok == 1
    assert result.ok is True
    assert result.decoded_frames == 3


def test_validate_rtsp_frames_invalid_min_frames_zero() -> None:
    result = validate_rtsp_frames(RTSP_URL, timeout_seconds=2, min_frames=0)

    assert result.frames_ok == 0
    assert result.ok is False
    assert result.returncode is None
    assert result.decoded_frames is None
    assert "min_frames" in result.error


def test_validate_rtsp_frames_invalid_min_frames_negative() -> None:
    result = validate_rtsp_frames(RTSP_URL, timeout_seconds=2, min_frames=-1)

    assert result.frames_ok == 0
    assert result.ok is False
    assert result.returncode is None
    assert result.decoded_frames is None
    assert "min_frames" in result.error
