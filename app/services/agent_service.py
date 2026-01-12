from typing import TypedDict, Literal, List, Dict, Optional
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
from app.services.vector_service import vector_service
import os

# Agent state definition:
class AgentState(TypedDict):
    query: str               #user's query
    intent: str              #user's intent('doc_question','greeting','general')
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
    prompt=f"""Classify this user query into ONE category:

Categories:
1. "document_question" - User asking about specific documents, company data, uploaded content
2. "greeting" - Simple greetings like hi, hello, how are you
3. "general" - General knowledge questions not related to documents

User query: "{query}"

Respond with ONLY the category name, nothing else."""
    response=llm.invoke(prompt)
    intent=response.content.strip().lower()

    #default to 'general' if unrecognized
    if intent not in ["document_question","greeting","general"]:
        intent="general" #fallback
    
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
    """Generate answer using LLM based on intent and retrieved chunks"""

    llm=get_llm()
    query=state["query"]
    intent=state["intent"]
    chunks=state.get("chunks",[])

    if intent == "document_question":
        if not chunks:
            answer="I'm sorry, I couldn't find any relevant information in the documents you provided."
            sources=[]
        else:
            # Build context from chunks
            context = "\n\n".join([
                f"[Document {chunk['doc_id']}, Chunk {chunk['chunk_id']}]:\n{chunk['text']}"
                for chunk in chunks
            ])
            prompt = f"""Answer the user's question using ONLY the information from these document chunks.
If the answer is not in the chunks, say so.

Document chunks:
{context}

User question: {query}

Answer:"""
            response=llm.invoke(prompt)
            answer=response.content.strip()

            #prepare sources for citation
            sources=[
                {
                    "doc_id":chunk["doc_id"],
                    "chunk_id":chunk["chunk_id"],
                    "similarity_score":chunk["similarity_score"]
                }
                for chunk in chunks[:3] #top 3 sources
            ]
    elif intent == "greeting":
        answer="Hello! How can I assist you today?"
        sources=[]
    else: #general
        prompt = f"""Answer this general knowledge question concisely:

{query}

Answer:"""
        response=llm.invoke(prompt)
        answer=response.content.strip()
        sources=[]
    
    state["answer"]=answer
    state["sources"]=sources
    return state

#router: decide which path to take based on intent
def route_by_intent(state:AgentState)->Literal["search","generate"]:
    """Decide next step based on intent"""
    intent=state["intent"]
    if intent=="document_question":
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
    final_state = agent_graph.invoke(initial_state)
    
    return {
        "query": final_state["query"],
        "answer": final_state["answer"],
        "sources": final_state["sources"]
    }
