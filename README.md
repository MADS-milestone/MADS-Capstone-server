# MADS Capstone server module

MADS Capstone back-end module with REST API.

## Run Postgres in Docker

`docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 --name postgres-pgvector pgvector/pgvector:pg16`

## Default Postgres parameters
- **username**: postgres
- **password**: postgres
- **host**: localhost
- **port**: 5432

## Start back-end module

> **NOTE:**  
> - run `pip install -r requirements.txt` to install dependencies  
> - create an `.env` file under `app` and add your OPENAI_API_KEY  

`cd app`  
`uvicorn main:app --host 127.0.0.1 --port 8080 --reload`

`--reload` option will restart the server automatically every time changes in the code are made

## Default URL of the back-end module:

`http://127.0.0.1:8080`

## REST API endpoints

- GET **/** - displays a silly greetings message
- GET **/hello/{name}** - displays a silly **Hello {name}!** message
- POST **/get_response/** - returns response for the query 
- GET **/reset_chat** - resets chat engine
- GET **/delete_index** - clears index
- GET **/get_index_length** - returns index length
- POST **/load_trials/** - downloads clinical trials and stores in the vector store
- GET **/load_pfizer_trials/** - downloads Pfizer (Phase 3, Interventional, Completed) clinical trials ans stores in the vector store

## Build and run the back-end module in Docker (run in the root dir)

`docker build -t ragapi-app .`  
`docker run -p 8080:8080 ragapi-app`
