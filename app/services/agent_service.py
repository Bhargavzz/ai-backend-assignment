from typing import TypedDict, Literal, List, Dict, Optional
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
from app.services.vector_service import vector_service
import os

# Agent state definition:
class AgentState(TypedDict):
    query: str               #user's query
    intent: str              #user's intent('search' or 'generate')
    chunks: List[Dict]       #retrieved document chunks
    answer: str              #generated answer
    sources: List[Dict]      #source metadata for citations
    user_id: Optional[int]   #filter search by user


#intitalise azure openai llm
def get_llm():
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=0.7
    )

#node-1:classify intent
def classify_intent(state: AgentState) -> AgentState:
    """Determine what type of query this is"""

    llm=get_llm()
    query=state["query"]
    prompt=f"""You are a precise routing agent for a RAG system.

Your job: Decide if the following user query requires searching through a database of documents.

Analyze the Query: "{query}"

Rules:
- RETURN "search" if the query asks for information, facts, summaries, specific details, or mentions "documents/files".
- RETURN "search" if it is a general knowledge question (e.g., "What is machine learning?") because the database might contain specific context.
- RETURN "generate" ONLY if the query is a greeting (hi, hello), a compliment, or pure small talk.

Output ONLY one word: "search" or "generate".
"""
    response=llm.invoke(prompt)
    intent=response.content.strip().lower()

    #default to search
    if intent not in ["search","generate"]:
        intent="search" #fallback
    
    state["intent"]=intent
    return state


#node-2: search documents(only for 'document_question' intent)
def search_documents(state: AgentState) -> AgentState:
    """query faiss to find relevant chunks"""

    query=state["query"]
    user_id=state.get("user_id")
    #search faiss with user filter
    chunks=vector_service.search(query, top_k=5, user_id=user_id)
    state["chunks"]=chunks
    return state

#node-3: generate answer
def generate_answer(state: AgentState) -> AgentState:
    """
    Generates the final answer.
    Handles both RAG (with context) and General Chat (no context).
    """
    llm = get_llm()
    query = state["query"]
    intent = state["intent"]
    chunks = state.get("chunks", [])

    sources = []

    # BRANCH 1: RAG (The "Search" Path)
    if intent == "search":
        if not chunks:
            # Sub-branch: Search happened but found nothing.
            # Fallback to general knowledge instead of just saying "I don't know".
            prompt = f"""The user asked: "{query}"

I searched their documents but found no relevant matches.
Please answer the question generally based on your own knowledge.
Start your answer by saying: "I couldn't find specific details in your documents, but generally..."
"""
            response = llm.invoke(prompt)
            answer = response.content.strip()
        else:
            # Sub-branch: Found documents. Use them.
            context = "\n\n".join([
                f"[Document {chunk['doc_id']}, Chunk {chunk['chunk_id']}]:\n{chunk['text']}"
                for chunk in chunks
            ])
            
            prompt = f"""You are a helpful assistant. Answer the user's question using ONLY the context provided below.
If the context doesn't contain the answer, say "I don't know based on the documents."

Context:
{context}

User Question: {query}
"""
            response = llm.invoke(prompt)
            answer = response.content.strip()
            
            # Prepare sources for the UI
            sources = [
                {
                    "doc_id": chunk["doc_id"],
                    "chunk_id": chunk.get("chunk_id", 0),
                    "similarity_score": chunk.get("similarity_score", 0.0)
                }
                for chunk in chunks[:3] # Limit to top 3 citations
            ]

    # BRANCH 2: General Chat (The "Generate" Path)
    else:
        prompt = f"""You are a helpful assistant. Reply to this user message politely.

User Message: {query}
"""
        response = llm.invoke(prompt)
        answer = response.content.strip()
        
    state["answer"] = answer
    state["sources"] = sources
    return state

#router: decide which path to take based on intent
def route_by_intent(state:AgentState)->Literal["search","generate"]:
    """Decide next step based on intent"""
    intent=state["intent"]
    if intent=="search":
        return "search" #go to search_documents node
    else:
        return "generate" #skip search, go to generate_answer node
    
#build the graph workflow
def create_agent_graph():
    """
    structure:
        START → classify_intent → route_by_intent
                                    ↓         ↓
                            search_documents  generate_answer
                                    ↓         ↓
                            generate_answer  END
                                    ↓
                                END
    """
    workflow=StateGraph(AgentState)
    #add nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("search_documents", search_documents)
    workflow.add_node("generate_answer", generate_answer)

    #set entry point
    workflow.set_entry_point("classify_intent")

    #add conditional routing after classify_intent
    workflow.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "search":"search_documents", #if document_question
            "generate":"generate_answer" #if greeting or general
        }
    )

    #afer search_docs, go to generate_answer
    workflow.add_edge("search_documents","generate_answer")

    #after generate ,go to end
    workflow.add_edge("generate_answer",END)
    return workflow.compile()


#gloabal agent instance
agent_graph=create_agent_graph()


#main function to invoke the agent
def ask_agent(query: str, user_id: int = None) -> Dict:
    """
    Main entry point for the agent.
    
    Args:
        query: User's question
        user_id: Optional user ID to filter document search
        
    Returns:
        {
            "query": "original question",
            "answer": "generated answer",
            "sources": [list of source metadata]
        }
    """
    # Initialize state
    initial_state: AgentState = {
        "query": query,
        "intent": "",
        "chunks": [],
        "answer": "",
        "sources": [],
        "user_id": user_id
    }
    
    # Run the graph
    try:

        final_state = agent_graph.invoke(initial_state)
    
        return {
            "query": final_state["query"],
            "answer": final_state["answer"],
            "sources": final_state["sources"],
            "intent": final_state["intent"]
        }
    except Exception as e:
        print(f"Agent error: {str(e)}")
        return{
            "query": query,
            "answer": "Sorry, I encountered an error while processing your request.",
            "sources": []   
        }
