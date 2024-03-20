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

> **NOTE:** First thing - create an `.env` file under `app` and add your OPENAI_API_KEY  

`cd app`  
`uvicorn main:app --host 127.0.0.1 --port 8080 --reload`

`--reload` option will restart the server automatically every time changes in the code are made

## Default URL of the back-end module:

`http://127.0.0.1:8080`

## REST API endpoints

- get **/** - displays a silly greetings message
- get **/hello/{name}** - displays a silly **Hello {name}!** message
- post **/get_response/** - returns response for the query 
- get **/reset_chat** - resets chat engine
- get **/delete_index** - clears index
- get **/get_index_length** - returns index length
- post **/load_trials/** - downloads clinical trials and stores in the vector store

## Build and run the back-end module in Docker
`cd app`  
`docker build -t ragapi-app .`  
`docker run -p 8080:8080 ragapi-app`
