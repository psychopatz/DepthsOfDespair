from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import StreamingResponse
from src.core.llm_service import LLMService
from src.schemas.ollama import (
    GenerateRequest,
    ChatRequest,
    EmbedRequest,
    ModelRequest,
    PullRequest,
)

router = APIRouter(
    prefix="/ollama",
    tags=["Ollama Management"]
)

def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service

async def handle_service_call(service_call, **kwargs):
    """
    Helper to wrap service calls, relaying specific HTTP exceptions
    and catching any other unexpected errors.
    """
    try:
        return await service_call(**kwargs)
    except HTTPException:
        # Re-raise HTTPException to let FastAPI handle it directly
        raise
    except Exception as e:
        # For any other unexpected exception, return a generic 500 error
        raise HTTPException(status_code=500, detail=f"An unexpected internal server error occurred: {str(e)}")

@router.post("/generate")
async def generate_completion(req: GenerateRequest, service: LLMService = Depends(get_llm_service)):
    result = await handle_service_call(service.generate_completion, prompt=req.prompt, stream=req.stream, options=req.options)
    return StreamingResponse(result, media_type="application/x-ndjson") if req.stream else result

@router.post("/chat")
async def generate_chat_completion(req: ChatRequest, service: LLMService = Depends(get_llm_service)):
    messages_dict = [msg.model_dump() for msg in req.messages]
    result = await handle_service_call(service.generate_chat_completion, messages=messages_dict, stream=req.stream, options=req.options)
    return StreamingResponse(result, media_type="application/x-ndjson") if req.stream else result

@router.post("/embeddings")
async def generate_embeddings(req: EmbedRequest, service: LLMService = Depends(get_llm_service)):
    return await handle_service_call(service.generate_embeddings, input_data=req.input, options=req.options)

@router.get("/list")
async def list_local_models(service: LLMService = Depends(get_llm_service)):
    return await handle_service_call(service.list_local_models)

@router.get("/ps")
async def list_running_models(service: LLMService = Depends(get_llm_service)):
    return await handle_service_call(service.list_running_models)

@router.post("/show")
async def show_model_info(req: ModelRequest, service: LLMService = Depends(get_llm_service)):
    return await handle_service_call(service.show_model_info, model_name=req.model)

@router.post("/pull")
async def pull_model(req: PullRequest, service: LLMService = Depends(get_llm_service)):
    result = await handle_service_call(service.pull_model, model_name=req.model, stream=req.stream)
    return StreamingResponse(result, media_type="application/x-ndjson") if req.stream else result

@router.delete("/delete")
async def delete_model(req: ModelRequest, service: LLMService = Depends(get_llm_service)):
    return await handle_service_call(service.delete_model, model_name=req.model)

@router.get("/version")
async def get_version(service: LLMService = Depends(get_llm_service)):
    return await handle_service_call(service.get_version)