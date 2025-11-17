import subprocess
from pathlib import Path
from collections.abc import Iterable
import shlex
import click
from rich.progress import track


@click.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--out-dir",
    "-o",
    default="proxies",
    type=click.Path(path_type=Path),
    help="Directory for proxy files.",
)
@click.option(
    "--scale",
    "-s",
    default="1280:-1",
    help='Scale filter, e.g. "1280:-1" or "960:-1".',
)
def main(input_path: Path, out_dir: Path, scale: str):
    for video_path in track(walk_path(input_path), description="Transcoding..."):
        relative_path = video_path.relative_to(input_path) if input_path.is_dir() else video_path.name
        output_path = out_dir / relative_path.parent / f"{relative_path.stem}.mov"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # check if output file already exists
        if output_path.exists():
            print(f"Skipping existing file: {output_path}")
            continue

        ffmpeg_cmd = (
            f'ffmpeg -i "{video_path}" -vf "scale={scale}" -threads 0 '
            f'-c:v prores_ks -profile:v 0 -qscale:v 12 -c:a pcm_s16le '
            f'-movflags +faststart+frag_keyframe+empty_moov "{output_path}"'
        )
        run_ffmpeg(ffmpeg_cmd)


def walk_path(input_path: Path) -> Iterable[Path]:
    """Yield all video files in the input path."""
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".mxf"}
    if input_path.is_file():
        if input_path.suffix.lower() in video_extensions:
            yield input_path
    else:
        for path in input_path.rglob("*"):
            if path.suffix.lower() in video_extensions:
                yield path


def run_ffmpeg(cmd: str):
    """Run an ffmpeg command and stream output."""
    print(f"Running: {cmd}")
    process = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in process.stdout or []:
        print(line, end="")

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg failed with code {process.returncode}")


if __name__ == "__main__":
    main()
