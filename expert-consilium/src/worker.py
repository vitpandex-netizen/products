from __future__ import annotations

import asyncio
import json
import logging

from src.config import settings
from src.core.openrouter import EXPERT_CONFIGS, OpenRouterClient
from src.core.smart_mode import determine_mode
from src.core.synthesizer import (
    SYNTHESIZER_SYSTEM_PROMPT,
    build_synthesizer_prompt,
    parse_synthesized_response,
)
from src.db.repository import ExpertResponseRepository, RequestRepository
from src.db.session import async_session_factory
from src.redis_client import ResultPublisher, TaskQueue, get_redis

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    """Run the worker process."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting worker...")

    redis = await get_redis()
    task_queue = TaskQueue(redis)
    result_publisher = ResultPublisher(redis)
    openrouter = OpenRouterClient()

    while True:
        try:
            messages = await task_queue.consume_tasks(
                group="consilium-workers",
                consumer="worker-1",
                batch_size=1,
            )

            for msg_id, msg_data in messages:
                # Parse task
                task = {
                    k: v for k, v in msg_data.items()
                }
                request_id = task.get("request_id", "")
                question = task.get("question", "")
                mode = task.get("mode", "basic")

                logger.info(f"Processing request {request_id} (mode={mode})")

                # Update status to processing
                async with async_session_factory() as session:
                    repo = RequestRepository(session)
                    await repo.update_status(request_id, "processing")

                # Query all experts in parallel
                expert_results = await openrouter.query_experts(question, mode)

                # Save each expert response to DB and publish
                total_cost = 0.0
                async with async_session_factory() as session:
                    resp_repo = ExpertResponseRepository(session)
                    for result in expert_results:
                        if result.get("error"):
                            logger.warning(f"Expert {result['role']} failed: {result['error']}")

                        db_resp = await resp_repo.create(
                            request_id=request_id,
                            role=result["role"],
                            model=result["model"],
                            response_text=result["response_text"],
                            tokens_in=result.get("tokens_in", 0),
                            tokens_out=result.get("tokens_out", 0),
                            cost=result.get("cost", 0.0),
                            latency_ms=result.get("latency_ms", 0),
                        )
                        total_cost += result.get("cost", 0.0)

                        # Publish partial result
                        await result_publisher.publish_expert_result(
                            request_id, result
                        )
                    await session.commit()

                # Run synthesizer
                logger.info(f"Running synthesizer for {request_id}")
                synth_model = (
                    settings.model_synthesizer_premium if mode == "premium"
                    else settings.model_synthesizer_basic
                )
                synth_prompt = build_synthesizer_prompt(question, expert_results)

                synth_result = {"content": "", "tokens_in": 0, "tokens_out": 0, "cost": 0.0, "latency_ms": 0}
                try:
                    synth_result = await openrouter.query_model(
                        synth_model, synth_prompt, SYNTHESIZER_SYSTEM_PROMPT
                    )
                    synthesized_text = synth_result["content"]
                    synth_cost = synth_result.get("cost", 0.0)
                    total_cost += synth_cost
                except Exception as e:
                    logger.error(f"Synthesizer failed: {e}")
                    # Fallback: simple concatenation
                    synthesized_text = "### 📋 Консенсус\n\n"
                    for r in expert_results:
                        if not r.get("error"):
                            synthesized_text += f"\n**{r['label']}:**\n{r['response_text'][:200]}...\n"
                    synthesized_text += "\n\n*Автоматическая сборка (синтезатор временно недоступен)*"
                    synth_cost = 0.0

                # Save synthesizer response
                synth_tokens_in = synth_result.get("tokens_in", 0)
                synth_tokens_out = synth_result.get("tokens_out", 0)
                synth_latency = synth_result.get("latency_ms", 0)

                async with async_session_factory() as session:
                    resp_repo = ExpertResponseRepository(session)
                    await resp_repo.create(
                        request_id=request_id,
                        role="synthesizer",
                        model=synth_model,
                        response_text=synthesized_text,
                        tokens_in=synth_tokens_in,
                        tokens_out=synth_tokens_out,
                        cost=synth_cost,
                        latency_ms=synth_latency,
                    )

                    # Mark request completed
                    repo = RequestRepository(session)
                    await repo.mark_completed(request_id)
                    await session.commit()

                # Publish final result
                parsed = parse_synthesized_response(synthesized_text)
                await result_publisher.publish_final_result(request_id, {
                    "synthesized_text": synthesized_text,
                    "confidence": parsed["confidence"],
                    "total_cost": total_cost,
                })

                # Acknowledge task
                await task_queue.ack_task(msg_id)
                logger.info(f"Completed request {request_id} (cost=${total_cost:.4f})")

        except Exception as e:
            logger.exception(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())