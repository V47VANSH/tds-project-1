import httpx
from app.models import EvaluationResponse
from app.utils.retry import create_retry_decorator
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EvaluatorService:
    def __init__(self):
        self.timeout = settings.evaluation_timeout
    
    @create_retry_decorator(max_attempts=10)
    async def send_evaluation(self, evaluation_url: str, data: EvaluationResponse) -> bool:
        """
        Send evaluation response with retry logic
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info(f"Sending evaluation to {evaluation_url}")
                
                response = await client.post(
                    evaluation_url,
                    json=data.model_dump(),
                )
                
                response.raise_for_status()
                logger.info(f"Evaluation sent successfully: {response.status_code}")
                return True
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error sending evaluation: {e}")
                raise
            except Exception as e:
                logger.error(f"Error sending evaluation: {e}")
                raise   