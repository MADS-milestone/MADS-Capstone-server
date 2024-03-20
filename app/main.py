from contextlib import asynccontextmanager

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from chatbot import ChatBot
from config import config
from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import JSONResponse

from index_management import IndexManager

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
    llm = OpenAI(temperature=0.001, model="gpt-3.5-turbo", max_tokens=512)
    Settings.llm = llm
    Settings.embed_model = embed_model
    index = ChatBot.get_index(config.connection_str, config.index_table, config.embed_dim)
    chat_engine = ChatBot.get_chat_engine(index)
    chat_engine.reset()
    app.state.chat_engine = chat_engine
    yield
    pass


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Welcome to Clinical Trials RAG!"}


@app.get("/hello/{name}")
async def hello(name: str):
    return JSONResponse(content={"message": f"Hello {name}!"})


@app.post("/get_response/")
async def get_response(query: str = Body()):
    response = app.state.chat_engine.chat(query)
    return JSONResponse(content={"detail": {"response": response.response}})


@app.get("/reset_chat")
async def reset_chat():
    app.state.chat_engine.reset()
    return JSONResponse(content={"detail": "chat engine reset"})


@app.get("/delete_index")
async def delete_index():
    try:
        IndexManager.delete_index(config.connection_str, f"data_{config.index_table}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting index: {str(e)}")
    return JSONResponse(content={"detail": "Index deleted"})


@app.get("/get_index_length")
async def get_index_length():
    try:
        idx_len = IndexManager.get_index_length(config.connection_str, f"data_{config.index_table}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting index length: {str(e)}")
    return JSONResponse(content={"detail": {"index_length": f"{idx_len}"}})


@app.post("/load_trials/")
async def get_trials(nct_ids: str = Body()):
    nct_id_list = [nct_id.strip() for nct_id in nct_ids.split(",")]

    try:
        index_manager = IndexManager(
            conn_str=config.connection_str,
            table_name=config.index_table,
            embed_dim=config.embed_dim)
        index_manager.load_trials(nct_id_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading trials: {str(e)}")
    try:
        idx_len = IndexManager.get_index_length(config.connection_str, f"data_{config.index_table}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting index length: {str(e)}")
    return JSONResponse(content={"detail": {"index_length": f"{idx_len}"}})
