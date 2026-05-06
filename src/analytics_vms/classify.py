"""Classification helpers for normalized camera status."""

STATUS_OK = "OK"
STATUS_NO_FRAMES = "NO_FRAMES"


def classify_frames(frames_ok: int) -> str:
    """Classify status using the central rule: OK when frames_ok equals 1."""
    if frames_ok == 1:
        return STATUS_OK
    return STATUS_NO_FRAMES
