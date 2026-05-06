"""Optional visual diagnostic detector tests."""

from __future__ import annotations

import subprocess
from typing import Any

from analytics_vms.visual_diagnostics import (
    VisualDiagnosticEvent,
    VisualDiagnosticResult,
    detect_black_frames,
    detect_frozen_frames,
)


RTSP_URL = "rtsp://192.0.2.10:554/Streaming/Channels/101"


def _mock_subprocess_run(
    monkeypatch: Any,
    *,
    expected_args: list[str],
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> None:
    """Mock subprocess.run with a CompletedProcess response."""

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert args == expected_args
        assert isinstance(args, list)
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["timeout"] == 2
        assert kwargs["check"] is False
        assert "shell" not in kwargs
        return subprocess.CompletedProcess(
            args=args,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr("analytics_vms.visual_diagnostics.subprocess.run", fake_run)


def _assert_video_mapping_after_input(args: list[str]) -> None:
    input_index = args.index("-i")
    map_index = args.index("-map")
    assert args[input_index + 1] == RTSP_URL
    assert map_index == input_index + 2
    assert args[map_index + 1] == "0:v:0"
    assert args[map_index + 2] == "-an"


def test_detect_black_frames_builds_expected_command(monkeypatch: Any) -> None:
    expected_args = [
        "ffmpeg",
        "-v",
        "info",
        "-rtsp_transport",
        "tcp",
        "-i",
        RTSP_URL,
        "-map",
        "0:v:0",
        "-an",
        "-t",
        "7",
        "-vf",
        "blackdetect=d=1.5:pix_th=0.2:pic_th=0.9",
        "-f",
        "null",
        "-",
    ]
    _mock_subprocess_run(monkeypatch, expected_args=expected_args)

    result = detect_black_frames(
        RTSP_URL,
        timeout_seconds=2,
        sample_seconds=7,
        min_black_duration_seconds=1.5,
        picture_black_threshold=0.9,
        pixel_black_threshold=0.2,
    )

    assert result == VisualDiagnosticResult(
        detector="blackdetect",
        process_ok=True,
        detected=0,
        events=(),
        timed_out=False,
        returncode=0,
        error="",
        raw_stdout="",
        raw_stderr="",
    )
    _assert_video_mapping_after_input(expected_args)
    assert expected_args[expected_args.index("-t") + 1] == "7"


def test_detect_frozen_frames_builds_expected_command(monkeypatch: Any) -> None:
    expected_args = [
        "ffmpeg",
        "-v",
        "info",
        "-rtsp_transport",
        "tcp",
        "-i",
        RTSP_URL,
        "-map",
        "0:v:0",
        "-an",
        "-t",
        "6",
        "-vf",
        "freezedetect=n=-55dB:d=3.0",
        "-f",
        "null",
        "-",
    ]
    _mock_subprocess_run(monkeypatch, expected_args=expected_args)

    result = detect_frozen_frames(
        RTSP_URL,
        timeout_seconds=2,
        sample_seconds=6,
        min_freeze_duration_seconds=3.0,
        noise_db="-55dB",
    )

    assert result.process_ok is True
    assert result.detected == 0
    assert result.events == ()
    _assert_video_mapping_after_input(expected_args)
    assert expected_args[expected_args.index("-t") + 1] == "6"


def test_detect_black_frames_parses_blackdetect_event(monkeypatch: Any) -> None:
    stderr = (
        "[blackdetect @ 0x1] black_start:0 "
        "black_end:2.5 black_duration:2.5"
    )
    expected_args = [
        "ffmpeg",
        "-v",
        "info",
        "-rtsp_transport",
        "tcp",
        "-i",
        RTSP_URL,
        "-map",
        "0:v:0",
        "-an",
        "-t",
        "5",
        "-vf",
        "blackdetect=d=1.0:pix_th=0.1:pic_th=0.98",
        "-f",
        "null",
        "-",
    ]
    _mock_subprocess_run(monkeypatch, expected_args=expected_args, stderr=stderr)

    result = detect_black_frames(RTSP_URL, timeout_seconds=2)

    assert result.process_ok is True
    assert result.detected == 1
    assert result.events == (
        VisualDiagnosticEvent(
            kind="black",
            start_seconds=0.0,
            end_seconds=2.5,
            duration_seconds=2.5,
        ),
    )


def test_detect_frozen_frames_parses_freezedetect_event(monkeypatch: Any) -> None:
    stderr = "\n".join(
        [
            "[freezedetect @ 0x1] lavfi.freezedetect.freeze_start: 1",
            "[freezedetect @ 0x1] lavfi.freezedetect.freeze_duration: 3.5",
            "[freezedetect @ 0x1] lavfi.freezedetect.freeze_end: 4.5",
        ]
    )
    expected_args = [
        "ffmpeg",
        "-v",
        "info",
        "-rtsp_transport",
        "tcp",
        "-i",
        RTSP_URL,
        "-map",
        "0:v:0",
        "-an",
        "-t",
        "5",
        "-vf",
        "freezedetect=n=-60dB:d=2.0",
        "-f",
        "null",
        "-",
    ]
    _mock_subprocess_run(monkeypatch, expected_args=expected_args, stderr=stderr)

    result = detect_frozen_frames(RTSP_URL, timeout_seconds=2)

    assert result.process_ok is True
    assert result.detected == 1
    assert result.events == (
        VisualDiagnosticEvent(
            kind="freeze",
            start_seconds=1.0,
            end_seconds=4.5,
            duration_seconds=3.5,
        ),
    )


def test_detect_black_frames_without_events_returns_not_detected(
    monkeypatch: Any,
) -> None:
    expected_args = [
        "ffmpeg",
        "-v",
        "info",
        "-rtsp_transport",
        "tcp",
        "-i",
        RTSP_URL,
        "-map",
        "0:v:0",
        "-an",
        "-t",
        "5",
        "-vf",
        "blackdetect=d=1.0:pix_th=0.1:pic_th=0.98",
        "-f",
        "null",
        "-",
    ]
    _mock_subprocess_run(
        monkeypatch,
        expected_args=expected_args,
        stderr="frame=1 fps=0.0 no diagnostic events",
    )

    result = detect_black_frames(RTSP_URL, timeout_seconds=2)

    assert result.process_ok is True
    assert result.detected == 0
    assert result.events == ()


def test_detect_black_frames_nonzero_returncode(monkeypatch: Any) -> None:
    password = "demo-secret"
    url = f"rtsp://admin:{password}@192.0.2.10:554/Streaming/Channels/101"

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert isinstance(args, list)
        assert "shell" not in kwargs
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout=f"stdout mentions {url}",
            stderr=f"stderr mentions {url} and {password}",
        )

    monkeypatch.setattr("analytics_vms.visual_diagnostics.subprocess.run", fake_run)

    result = detect_black_frames(url, timeout_seconds=2)

    assert result.process_ok is False
    assert result.detected == 0
    assert result.events == ()
    assert result.returncode == 1
    assert "return code 1" in result.error
    assert password not in result.error
    assert password not in result.raw_stdout
    assert password not in result.raw_stderr
    assert "rtsp://admin:***@192.0.2.10:554/Streaming/Channels/101" in result.error


def test_detect_frozen_frames_timeout(monkeypatch: Any) -> None:
    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=args,
            timeout=kwargs["timeout"],
            output="partial stdout",
            stderr="partial stderr",
        )

    monkeypatch.setattr("analytics_vms.visual_diagnostics.subprocess.run", fake_run)

    result = detect_frozen_frames(RTSP_URL, timeout_seconds=2)

    assert result.detector == "freezedetect"
    assert result.process_ok is False
    assert result.detected == 0
    assert result.events == ()
    assert result.timed_out is True
    assert result.returncode is None
    assert "timed out" in result.error


def test_detect_black_frames_file_not_found(monkeypatch: Any) -> None:
    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError

    monkeypatch.setattr("analytics_vms.visual_diagnostics.subprocess.run", fake_run)

    result = detect_black_frames(RTSP_URL, timeout_seconds=2)

    assert result.process_ok is False
    assert result.detected == 0
    assert result.events == ()
    assert result.returncode is None
    assert result.error == "ffmpeg executable not found."


def test_detect_frozen_frames_masks_encoded_and_decoded_password_tokens(
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

    monkeypatch.setattr("analytics_vms.visual_diagnostics.subprocess.run", fake_run)

    result = detect_frozen_frames(url, timeout_seconds=2)

    assert result.process_ok is False
    assert encoded_password not in result.error
    assert encoded_password not in result.raw_stdout
    assert encoded_password not in result.raw_stderr
    assert decoded_password not in result.error
    assert decoded_password not in result.raw_stdout
    assert decoded_password not in result.raw_stderr


def test_detect_black_frames_invalid_sample_seconds_skips_subprocess(
    monkeypatch: Any,
) -> None:
    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError("subprocess.run should not be called")

    monkeypatch.setattr("analytics_vms.visual_diagnostics.subprocess.run", fake_run)

    result = detect_black_frames(RTSP_URL, timeout_seconds=2, sample_seconds=0)

    assert result.detector == "blackdetect"
    assert result.process_ok is False
    assert result.detected == 0
    assert result.events == ()
    assert result.returncode is None
    assert "sample_seconds" in result.error


def test_detect_frozen_frames_invalid_duration_skips_subprocess(
    monkeypatch: Any,
) -> None:
    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError("subprocess.run should not be called")

    monkeypatch.setattr("analytics_vms.visual_diagnostics.subprocess.run", fake_run)

    result = detect_frozen_frames(
        RTSP_URL,
        timeout_seconds=2,
        min_freeze_duration_seconds=0,
    )

    assert result.detector == "freezedetect"
    assert result.process_ok is False
    assert result.detected == 0
    assert result.events == ()
    assert result.returncode is None
    assert "min_freeze_duration_seconds" in result.error
