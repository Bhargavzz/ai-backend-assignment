from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.services.agent_service import ask_agent

router=APIRouter(prefix="/ai", tags=["AI Agent"])

@router.post("/ask", response_model=schemas.AskResponse)
def ask_question(request: schemas.AskRequest):
    """
    Ask the AI agent a question

    Agent has to:
    1.classify your intent(doc ques,greeting, or general)
    2.search relevant docs if needed
    3.generate ans using azure openai
    """
    try:
        result = ask_agent(request.query)

        return schemas.AskResponse(
            query=result["query"],
            answer=result["answer"],
            sources=[
                schemas.SourceMetadata(**source) for source in result["sources"]
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Agent error: {str(e)}")

