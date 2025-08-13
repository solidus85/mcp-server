import logging
import json
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import uuid
from functools import wraps
import time
import asyncio
from logging.handlers import RotatingFileHandler
from pythonjsonlogger.json import JsonFormatter


def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = True,
) -> logging.Logger:
    """Set up logging with optional JSON formatting and file output"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers = []  # Clear existing handlers

    # Create formatters
    if json_format:
        formatter = JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            timestamp=True,
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix"""
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def hash_text(text: str) -> str:
    """Generate SHA256 hash of text"""
    return hashlib.sha256(text.encode()).hexdigest()


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()


def retry_async(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying async functions with exponential backoff"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise e

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


def retry_sync(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying synchronous functions with exponential backoff"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise e

                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks"""
    import re

    # Remove any path components
    filename = Path(filename).name

    # Remove special characters
    filename = re.sub(r"[^\w\s\-\.]", "", filename)

    # Replace spaces with underscores
    filename = filename.replace(" ", "_")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = f"{name[:max_name_length]}.{ext}" if ext else name[:max_name_length]

    return filename


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load JSON file with error handling"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def save_json_file(data: Dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """Save data to JSON file"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


class Timer:
    """Context manager for timing operations"""

    def __init__(self, name: str = "Operation", logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start
        message = f"{self.name} took {self.elapsed:.4f} seconds"
        if self.logger:
            self.logger.info(message)
        else:
            print(message)


def validate_api_key(api_key: Optional[str], provider: str) -> bool:
    """Validate that an API key is present and properly formatted"""
    if not api_key:
        return False

    # Basic validation for known providers
    if provider == "openai":
        return api_key.startswith("sk-") and len(api_key) > 20
    elif provider == "anthropic":
        return api_key.startswith("sk-ant-") and len(api_key) > 20

    # Default: just check if key is not empty
    return len(api_key) > 0