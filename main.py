import subprocess
from pathlib import Path
from tqdm import tqdm
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Function to check if a file is already in HEVC format
def is_hevc(file_path):
    """
    Check if a video file is already encoded in HEVC format.

    Args:
        file_path (Path): The path to the video file.

    Returns:
        bool: True if the file is in HEVC format, False otherwise.
    """
    try:
        codec_info = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "csv=p=0",
                str(file_path),
            ]
        )
        return b"hevc" in codec_info.lower() or b"h265" in codec_info.lower()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking file: {file_path}")
        logger.error(e)
        return False


# Function to transcode a video file to HEVC
def transcode_to_hevc(input_file):
    """
    Transcode a video file to HEVC format.

    Args:
        input_file (Path): The path to the input video file.

    Returns:
        Path: The path to the output HEVC-encoded file.
    """
    output_file = input_file.with_suffix(".mp4")
    input_path = str(input_file)
    output_path = str(output_file)

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            input_path,
            "-c:v",
            "libx265",
            "-crf",
            "23",
            "-preset",
            "medium",
            "-vf",
            "scale=min(iw\\,1920):-2",  # Limit resolution to 1080p
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",  # Enable faststart for streaming
            "-pix_fmt",
            "yuv420p",  # Optimal pixel format for compatibility
            "-profile:v",
            "main",  # Main profile for wider compatibility
            "-level",
            "4.0",  # Level 4.0 for compatibility with Google TV
            output_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return output_file


# Main function
def main(target_directory, dry_run=False):
    """
    Main function to transcode video files in a target directory to HEVC format.

    Args:
        target_directory (str): The target directory to search for video files.
        dry_run (bool, optional): If True, only preview the number of files to be transcoded (no actual transcoding).

    Returns:
        None
    """
    target_directory = Path(target_directory)
    video_extensions = (".mp4", ".mkv", ".avi")
    video_files = [
        file
        for file in target_directory.glob("**/*.*")
        if file.suffix.lower() in video_extensions
    ]
    total_files = len(video_files)
    transcode_count = 0

    if dry_run:
        logger.info(f"Total files found: {total_files}")
        logger.info("Calculating files to be transcoded...")

        for video_file in tqdm(video_files, desc="Checking", unit="file"):
            if not is_hevc(video_file):
                transcode_count += 1

        logger.info(
            f"{transcode_count}/{total_files} files would be transcoded ({(transcode_count / total_files) * 100:.2f}%)."
        )
        return

    for video_file in tqdm(video_files, desc="Transcoding", unit="file"):
        if not is_hevc(video_file):
            transcode_to_hevc(video_file)
            transcode_count += 1

    logger.info(
        f"Transcoding complete. {transcode_count}/{total_files} files transcoded."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch transcode video files to HEVC.")
    parser.add_argument(
        "target_directory", help="Target directory to search for video files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the number of files to be transcoded (no actual transcoding)",
    )
    args = parser.parse_args()

    main(args.target_directory, args.dry_run)
