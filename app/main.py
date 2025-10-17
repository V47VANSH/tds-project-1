from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.models import TaskRequest, TaskResponse
from app.config import settings
from app.services.llm_service import LLMService
from app.services.github_service import GitHubService
from app.services.evaluator import EvaluatorService
from app.models import EvaluationResponse
import logging
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Automated Task Handler",
    description="API for automated app generation and deployment",
    version="1.0.0"
)

llm_service = LLMService()
github_service = GitHubService()
evaluator_service = EvaluatorService()


async def process_task(task_request: TaskRequest):
    """
    Background task to process the request
    """
    try:
        logger.info(f"Processing task: {task_request.task}, Round: {task_request.round}")
        logger.info(f"Checks to pass: {task_request.checks}")
        
        repo_name = task_request.task
        
        # Step 0: For round 2+, get previous rounds data and current repo files
        previous_rounds = None
        repo_files = None
        
        if task_request.round >= 2:
            logger.info(f"Fetching previous rounds data and repo files for round {task_request.round}")
            previous_rounds = await github_service.get_previous_rounds_data(repo_name, task_request.round)
            repo_files = await github_service.get_repo_files(repo_name)
        
        # Step 1: Generate app using LLM
        files = await llm_service.generate_app(
            task_request.brief,
            task_request.attachments,
            task_request.round,
            previous_rounds,
            repo_files,
            task_request.checks
        )
        
        # Step 2: Generate README
        readme = await llm_service.generate_readme(
            task_request.task,
            task_request.brief,
            task_request.round
        )
        files["README.md"] = readme
        
        # Step 3: Create/update GitHub repository
        if task_request.round == 1:
            repo_url = await github_service.create_repository(
                repo_name,
                f"Automated app: {task_request.brief[:100]}"
            )
        else:
            repo_url = f"https://github.com/{settings.github_username}/{repo_name}"
        
        # Step 4: Add MIT License
        await github_service.add_mit_license(repo_name)
        
        # Step 5: Push files
        commit_message = f"Round {task_request.round}: {task_request.brief[:50]}"
        commit_sha = await github_service.push_files(repo_name, files, commit_message)
        
        # Step 6: Store current round data in the repo
        await github_service.store_round_data(
            repo_name,
            task_request.round,
            task_request.brief,
            task_request.checks,
            task_request.attachments
        )
        
        # Step 7: Enable GitHub Pages
        pages_url = await github_service.enable_github_pages(repo_name)
        
        # Step 8: Wait for Pages to deploy
        await asyncio.sleep(10)
        
        # Step 9: Send evaluation
        evaluation_data = EvaluationResponse(
            email=task_request.email,
            task=task_request.task,
            round=task_request.round,
            nonce=task_request.nonce,
            repo_url=repo_url,
            commit_sha=commit_sha,
            pages_url=pages_url
        )
        
        await evaluator_service.send_evaluation(
            task_request.evaluation_url,
            evaluation_data
        )
        
        logger.info(f"Task completed successfully: {task_request.task}, Round: {task_request.round}")
        
    except Exception as e:
        logger.error(f"Error processing task: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "message": "Automated Task Handler API is running",
        "version": "1.0.0"
    }


@app.post("/task", response_model=TaskResponse)
async def handle_task(
    task_request: TaskRequest,
    background_tasks: BackgroundTasks
):
    """
    Main endpoint to receive and process tasks
    """
    # Print and log the full incoming request payload
    try:
        payload_json = task_request.json()
    except Exception:
        payload_json = str(task_request)
    logger.info(f"Request received at /task: {payload_json}")
    print(f"Request received at /task: {payload_json}")

    # Verify secret
    if task_request.secret != settings.secret_key:
        logger.warning(f"Invalid secret received for task: {task_request.task}")
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    logger.info(f"Received task: {task_request.task}, Round: {task_request.round}")
    
    # Process task in background
    background_tasks.add_task(process_task, task_request)
    
    return TaskResponse(
        status="accepted",
        message=f"Task {task_request.task} accepted for processing (Round {task_request.round})",
        task=task_request.task,
        round=task_request.round
    )


@app.get("/health")
async def health_check():
    """
    Detailed health check
    """
    return {
        "status": "healthy",
        "github_configured": bool(settings.github_token),
        "llm_configured": bool(settings.llm_api_key),
        "username": settings.github_username
    }


# Add a handler to log validation errors and the raw request body
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        raw_body = (await request.body()).decode("utf-8")
    except Exception:
        raw_body = "<could not read body>"
    logger.error(f"Request validation error: {exc.errors()}")
    logger.error(f"Raw request body: {raw_body}")
    print(f"Request validation error: {exc.errors()}")
    print(f"Raw request body: {raw_body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "raw_body": raw_body},
    )

# uv run uvicorn app.main:app --reload --port 8000