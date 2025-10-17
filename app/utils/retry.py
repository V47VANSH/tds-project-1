from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx
import logging

logger = logging.getLogger(__name__)


def create_retry_decorator(max_attempts: int = 10):
    """
    Create a retry decorator with exponential backoff: 1, 2, 4, 8... seconds
    """
    return retry(
        retry=retry_if_exception_type((httpx.HTTPError, ConnectionError)),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(max_attempts),
        before_sleep=lambda retry_state: logger.info(
            f"Retrying after {retry_state.next_action.sleep} seconds... (attempt {retry_state.attempt_number})"
        ),
    )