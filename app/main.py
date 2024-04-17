from contextlib import asynccontextmanager

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from starlette.responses import FileResponse

from chatbot import ChatBot
from config import config
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.responses import JSONResponse

from index_management import IndexManager
from utils import init_logging, build_query

load_dotenv()

logger = init_logging(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing models, index and chatbot...")
    embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    llm = OpenAI(temperature=0.001, model="gpt-3.5-turbo-0125", max_tokens=512)
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
    return {"message": "Welcome to the UMSI Clinical Trials RAG!"}


@app.get("/hello/{name}")
async def hello(name: str):
    return JSONResponse(content={"message": f"Hello {name}!"})


@app.post("/get_response/")
async def get_response(payload_req: Request):
    payload = await payload_req.json()
    print(payload)
    logger.info(f"Received a POST request, query: {payload['query']}, profile: {payload['profile']}")
    query = build_query(payload)
    response = app.state.chat_engine.chat(query)
    return JSONResponse(content={"response": response.response})


@app.get("/reset_chat")
async def reset_chat():
    logger.info("Resetting chat bot...")
    app.state.chat_engine.reset()
    logger.info("Chat bot reset.")
    return JSONResponse(content={"detail": "chat engine reset"})


@app.get("/delete_index")
async def delete_index():
    try:
        logger.info("Deleting index...")
        IndexManager.delete_index(config.connection_str, f"{config.index_table}")
        logger.info("Index deleted.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting index: {str(e)}")
    return JSONResponse(content={"detail": "Index deleted"})


@app.get("/get_index_length")
async def get_index_length():
    try:
        logger.info("Getting index length...")
        idx_len = IndexManager.get_index_length(config.connection_str, f"data_{config.index_table}")
        logger.info(f"Index length: {idx_len}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting index length: {str(e)}")
    return JSONResponse(content={"index_length": f"{idx_len}"})


@app.post("/load_trials/")
async def get_trials(nct_ids: str = Body()):
    nct_id_list = [nct_id.strip() for nct_id in nct_ids.split(",")]
    logger.info(f"Getting trials for the given nct_ids list of length: {len(nct_id_list)}...")

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
    return JSONResponse(content={"index_length": f"{idx_len}"})

@app.get("/load_pfizer_trials/")
async def get_pfizer_trials():
    try:
        index_manager = IndexManager(
            conn_str=config.connection_str,
            table_name=config.index_table,
            embed_dim=config.embed_dim
        )
        logger.info("Pulling NCT IDs of Pfizer trials from AACT...")
        pfizer_ncts = index_manager.pull_pfizer_trials()
        logger.info(f"{len(pfizer_ncts)} trials pulled")
        logger.info("Storing Pfizer trials into index...")
        index_manager.load_trials(pfizer_ncts)
        logger.info("Done")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading trials: {str(e)}")
    try:
        idx_len = IndexManager.get_index_length(config.connection_str, f"data_{config.index_table}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting index length: {str(e)}")
    return JSONResponse(content={"index_length": f"{idx_len}"})


@app.get("/get_trials_for_condition/{condition}")
async def get_trials_for_condition(condition: str):
    try:
        index_manager = IndexManager(
            conn_str=config.connection_str,
            table_name=config.index_table,
            embed_dim=config.embed_dim
        )
        logger.info(f"Getting most recent Pfizer trial for {condition}...")
        res = index_manager.get_most_recent_trial(condition)
        if len(res) == 0:
            logger.info(f"No clinical trials found for {condition}.")
            return JSONResponse(
                content={"detail": {"results_found": False}}
            )
        else:
            logger.info(f"{len(res)} trials found for {condition}")
        return JSONResponse(
            content={"detail": {"results_found": True, "trials": res}}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting most recent trial: {str(e)}")
