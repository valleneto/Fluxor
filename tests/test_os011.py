"""OS011 local-media policy regression; no user files are touched."""
from pathlib import Path
from tempfile import TemporaryDirectory
from fluxor_core.media_policy import media_kind, cloud_risk, preview_allowed

def main():
    assert media_kind("cut.MP4") == "video"
    assert media_kind("photo.HEIC") == "image"
    assert media_kind("notes.txt") == "other"
    assert cloud_risk("/Users/test/Library/CloudStorage/Drive/cut.mp4")
    assert not cloud_risk("/tmp/cut.mp4")
    with TemporaryDirectory() as temp:
        root = Path(temp)
        movie = root / "preview.mp4"
        movie.write_bytes(b"synthetic-not-a-real-movie")
        assert preview_allowed(movie)
        assert not preview_allowed(root / "missing.mp4")
        link = root / "linked.mp4"
        link.symlink_to(movie)
        assert not preview_allowed(link)
        assert movie.read_bytes() == b"synthetic-not-a-real-movie"
    print("OS011 local-only media policy passed")

if __name__ == "__main__":
    main()
