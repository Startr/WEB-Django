#!/usr/bin/env python
"""
Script to move media files from their current locations to the new media directory structure.
Run this script from the project root directory.
"""

import os
import shutil
from pathlib import Path

def ensure_dir(directory):
    """Make sure the directory exists."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def move_files(source_dir, dest_dir, file_pattern='*'):
    """Move files from source to destination directory."""
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Source directory {source_dir} does not exist. Skipping.")
        return

    ensure_dir(dest_dir)
    
    files = list(source_path.glob(file_pattern))
    if not files:
        print(f"No files found in {source_dir} matching pattern {file_pattern}")
        return
    
    for file_path in files:
        print(f"Moving {file_path} to {dest_dir}")
        try:
            shutil.move(str(file_path), dest_dir)
        except Exception as e:
            print(f"Error moving {file_path}: {e}")

def main():
    # Define the base project directory
    base_dir = Path(__file__).resolve().parent
    
    # Create the media directory if it doesn't exist
    media_dir = base_dir / 'media'
    ensure_dir(media_dir)
    
    # Move profile pictures
    profile_pictures_dir = media_dir / 'profile_pictures'
    move_files(base_dir / 'profile_pictures', profile_pictures_dir)
    
    # Move logos
    logos_dir = media_dir / 'logos'
    move_files(base_dir / 'logos', logos_dir)
    
    # Move backgrounds
    backgrounds_dir = media_dir / 'backgrounds'
    move_files(base_dir / 'backgrounds', backgrounds_dir)
    
    # Move badges
    badges_dir = media_dir / 'badges'
    move_files(base_dir / 'badges', badges_dir)
    
    print("Media file migration complete.")

if __name__ == "__main__":
    main() 