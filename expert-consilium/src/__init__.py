# Expert Consilium

from src.config import settings
from src.db.models import Request, ExpertResponse, Feedback
from src.db.session import get_session, init_db, async_session_factory
from src.db.repository import RequestRepository, ExpertResponseRepository, FeedbackRepository
from src.redis_client import get_redis, close_redis, TaskQueue, ResultPublisher
from src.core.openrouter import OpenRouterClient, EXPERT_CONFIGS
from src.core.smart_mode import determine_mode, calculate_complexity_score, is_complex_query
from src.core.schemas import RequestCreate, RequestResponse, ExpertResponseSchema, HealthResponse
from src.core.synthesizer import build_synthesizer_prompt, parse_synthesized_response, SYNTHESIZER_SYSTEM_PROMPT