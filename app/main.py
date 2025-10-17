from fastapi import FastAPI, HTTPException, BackgroundTasks
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
        
        # Step 1: Generate app using LLM
        files = await llm_service.generate_app(
            task_request.brief,
            task_request.attachments,
            task_request.round
        )
        
        # Step 2: Generate README
        readme = await llm_service.generate_readme(
            task_request.task,
            task_request.brief,
            task_request.round
        )
        files["README.md"] = readme
        
        # Step 3: Create/update GitHub repository
        repo_name = task_request.task
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
        
        # Step 6: Enable GitHub Pages
        pages_url = await github_service.enable_github_pages(repo_name)
        
        # Step 7: Wait a bit for Pages to deploy
        await asyncio.sleep(5)
        
        # Step 8: Send evaluation
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