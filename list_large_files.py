#!/usr/bin/env python3
"""
Script to list all files exceeding 400 lines in src, web, and tests directories
"""

import os
from pathlib import Path
from typing import List, Tuple

def count_lines(file_path: Path) -> int:
    """Count the number of lines in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def find_large_files(directories: List[str], line_threshold: int = 400) -> List[Tuple[Path, int]]:
    """Find all files exceeding the line threshold in specified directories"""
    large_files = []
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"Warning: Directory {directory} does not exist")
            continue
            
        # Walk through all files recursively
        for file_path in dir_path.rglob('*'):
            # Skip directories and common non-code files
            if file_path.is_dir():
                continue
                
            # Skip binary files and common non-code extensions
            skip_extensions = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe', 
                              '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg',
                              '.woff', '.woff2', '.ttf', '.eot',
                              '.pdf', '.zip', '.tar', '.gz', '.db'}
            if file_path.suffix.lower() in skip_extensions:
                continue
                
            # Skip __pycache__ and .git directories
            if '__pycache__' in str(file_path) or '.git' in str(file_path):
                continue
                
            # Count lines
            line_count = count_lines(file_path)
            if line_count > line_threshold:
                large_files.append((file_path, line_count))
    
    return large_files

def main():
    """Main function"""
    # Directories to scan
    directories = ['src', 'web', 'tests']
    line_threshold = 400
    
    print(f"Scanning for files with more than {line_threshold} lines...")
    print(f"Directories: {', '.join(directories)}")
    print("-" * 80)
    
    # Find large files
    large_files = find_large_files(directories, line_threshold)
    
    if not large_files:
        print(f"No files found exceeding {line_threshold} lines.")
        return
    
    # Sort by line count (descending)
    large_files.sort(key=lambda x: x[1], reverse=True)
    
    # Display results
    print(f"\nFound {len(large_files)} files exceeding {line_threshold} lines:\n")
    print(f"{'File Path':<60} {'Lines':>10}")
    print("-" * 72)
    
    total_lines = 0
    for file_path, line_count in large_files:
        # Make path relative to current directory for cleaner output
        try:
            relative_path = file_path.relative_to(Path.cwd())
        except ValueError:
            relative_path = file_path
            
        print(f"{str(relative_path):<60} {line_count:>10,}")
        total_lines += line_count
    
    print("-" * 72)
    print(f"{'Total lines in large files:':<60} {total_lines:>10,}")
    print(f"{'Average lines per file:':<60} {total_lines // len(large_files):>10,}")
    
    # Additional statistics
    print("\n" + "=" * 72)
    print("File Type Breakdown:")
    print("-" * 72)
    
    # Group by extension
    by_extension = {}
    for file_path, line_count in large_files:
        ext = file_path.suffix or 'no extension'
        if ext not in by_extension:
            by_extension[ext] = {'count': 0, 'lines': 0}
        by_extension[ext]['count'] += 1
        by_extension[ext]['lines'] += line_count
    
    print(f"{'Extension':<20} {'Files':>10} {'Total Lines':>15}")
    print("-" * 48)
    for ext, stats in sorted(by_extension.items(), key=lambda x: x[1]['lines'], reverse=True):
        print(f"{ext:<20} {stats['count']:>10} {stats['lines']:>15,}")

if __name__ == "__main__":
    main()