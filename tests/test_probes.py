"""ffprobe wrapper tests."""

from __future__ import annotations

import json
import math
import subprocess
from typing import Any

from analytics_vms.probes import ProbeResult, run_ffprobe


RTSP_URL = "rtsp://192.0.2.10:554/Streaming/Channels/101"


def _ffprobe_json(stream: dict[str, Any] | None) -> str:
    """Build ffprobe-like JSON for one optional stream."""
    streams = [] if stream is None else [stream]
    return json.dumps({"streams": streams})


def _mock_subprocess_run(
    monkeypatch: Any,
    *,
    stdout: str,
    stderr: str = "",
    returncode: int = 0,
) -> None:
    """Mock subprocess.run with a CompletedProcess response."""

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert args == [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,avg_frame_rate,r_frame_rate",
            "-of",
            "json",
            RTSP_URL,
        ]
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

    monkeypatch.setattr("analytics_vms.probes.subprocess.run", fake_run)


def test_run_ffprobe_success_with_valid_video_json(monkeypatch: Any) -> None:
    _mock_subprocess_run(
        monkeypatch,
        stdout=_ffprobe_json(
            {
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "25/1",
                "r_frame_rate": "25/1",
            }
        ),
    )

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result == ProbeResult(
        ok=True,
        timed_out=False,
        returncode=0,
        error="",
        raw_stdout=result.raw_stdout,
        raw_stderr="",
        has_video=True,
        video_codec="h264",
        width=1920,
        height=1080,
        fps=25.0,
    )


def test_run_ffprobe_avg_frame_rate_25(monkeypatch: Any) -> None:
    _mock_subprocess_run(
        monkeypatch,
        stdout=_ffprobe_json({"avg_frame_rate": "25/1"}),
    )

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.fps == 25.0


def test_run_ffprobe_avg_frame_rate_ntsc(monkeypatch: Any) -> None:
    _mock_subprocess_run(
        monkeypatch,
        stdout=_ffprobe_json({"avg_frame_rate": "30000/1001"}),
    )

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.fps is not None
    assert math.isclose(result.fps, 29.97, rel_tol=0.001)


def test_run_ffprobe_zero_frame_rate_is_none(monkeypatch: Any) -> None:
    _mock_subprocess_run(
        monkeypatch,
        stdout=_ffprobe_json({"avg_frame_rate": "0/0"}),
    )

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.fps is None


def test_run_ffprobe_na_frame_rate_is_none(monkeypatch: Any) -> None:
    _mock_subprocess_run(
        monkeypatch,
        stdout=_ffprobe_json({"avg_frame_rate": "N/A"}),
    )

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.fps is None


def test_run_ffprobe_no_video_stream(monkeypatch: Any) -> None:
    _mock_subprocess_run(monkeypatch, stdout=_ffprobe_json(None))

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.ok is False
    assert result.has_video is False
    assert "video stream" in result.error


def test_run_ffprobe_nonzero_returncode(monkeypatch: Any) -> None:
    _mock_subprocess_run(
        monkeypatch,
        stdout="",
        stderr="RTSP negotiation failed",
        returncode=1,
    )

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.ok is False
    assert result.returncode == 1
    assert "return code 1" in result.error


def test_run_ffprobe_timeout(monkeypatch: Any) -> None:
    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=args,
            timeout=kwargs["timeout"],
            output="partial stdout",
            stderr="partial stderr",
        )

    monkeypatch.setattr("analytics_vms.probes.subprocess.run", fake_run)

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.ok is False
    assert result.timed_out is True
    assert result.returncode is None
    assert "timed out" in result.error


def test_run_ffprobe_file_not_found(monkeypatch: Any) -> None:
    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError

    monkeypatch.setattr("analytics_vms.probes.subprocess.run", fake_run)

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.ok is False
    assert result.returncode is None
    assert result.error == "ffprobe executable not found."


def test_run_ffprobe_invalid_json(monkeypatch: Any) -> None:
    _mock_subprocess_run(monkeypatch, stdout="{not-json")

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.ok is False
    assert "invalid JSON" in result.error


def test_run_ffprobe_masks_password_in_outputs(monkeypatch: Any) -> None:
    password = "demo-secret"
    url = f"rtsp://admin:{password}@192.0.2.10:554/Streaming/Channels/101"

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout=f"stdout mentions {url}",
            stderr=f"stderr mentions {url} and {password}",
        )

    monkeypatch.setattr("analytics_vms.probes.subprocess.run", fake_run)

    result = run_ffprobe(url, timeout_seconds=2)

    assert result.ok is False
    assert password not in result.error
    assert password not in result.raw_stdout
    assert password not in result.raw_stderr
    assert "rtsp://admin:***@192.0.2.10:554/Streaming/Channels/101" in result.raw_stdout


def test_run_ffprobe_sanitizer_handles_malformed_rtsp_url(monkeypatch: Any) -> None:
    password = "demo-secret"
    malformed_url = f"rtsp://admin:{password}@[bad/Streaming/Channels/101"

    def fake_mask_rtsp_url(_value: str) -> str:
        raise ValueError("bad rtsp url")

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr=f"stderr mentions {malformed_url}",
        )

    monkeypatch.setattr("analytics_vms.probes.mask_rtsp_url", fake_mask_rtsp_url)
    monkeypatch.setattr("analytics_vms.probes.subprocess.run", fake_run)

    result = run_ffprobe(RTSP_URL, timeout_seconds=2)

    assert result.ok is False
    assert password not in result.error
    assert password not in result.raw_stderr
    assert "rtsp://admin:***@[bad/Streaming/Channels/101" in result.raw_stderr


def test_run_ffprobe_masks_url_encoded_and_decoded_password_tokens(
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

    monkeypatch.setattr("analytics_vms.probes.subprocess.run", fake_run)

    result = run_ffprobe(url, timeout_seconds=2)

    assert result.ok is False
    assert encoded_password not in result.error
    assert encoded_password not in result.raw_stdout
    assert encoded_password not in result.raw_stderr
    assert decoded_password not in result.error
    assert decoded_password not in result.raw_stdout
    assert decoded_password not in result.raw_stderr
