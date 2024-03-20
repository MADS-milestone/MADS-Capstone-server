from dotenv import load_dotenv
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url

load_dotenv()

class ChatBot:

    def __init__(self, conn_str, index_table):
        self.conn_str = conn_str
        self.index_table = index_table

    @classmethod
    def get_index(cls, conn_str, index_table, embed_dim):
        url = make_url(conn_str)

        hybrid_vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name=index_table,
            embed_dim=embed_dim,
            hybrid_search=True,
            text_search_config="english"
        )

        index = VectorStoreIndex.from_vector_store(
            vector_store=hybrid_vector_store
        )

        return index

    @classmethod
    def get_chat_engine(cls, index):
        memory = ChatMemoryBuffer.from_defaults(token_limit=10_000)  # <== adjust
        # chat_engine.reset()

        chat_engine = index.as_chat_engine(
            similarity_top_k=7,  # <== adjust
            chat_mode="condense_plus_context",
            vector_store_query_mode="hybrid",
            sparse_top_k=2,
            memory=memory,
            context_prompt=(
                """
                You are a chatbot, who is an expert in parsing information from clinical trials.
                If you are asked for a brief summary, then provide a concise response.
                If you are asked for a Plain Language Summary (PLS), then use everyday language to make the clinical results of a study meaningful and understandable to a lay person.
                If you are asked for a expert summary, then emulate a PhD scientist and expert statistician in your response.
                If you are asked for a child-friendly answer, then emulate a kindergarten teacher and use language a child can understand.
                """
                "Here are the relevant documents for the context:\n"
                "{context_str}"
                "\nInstruction: Only use the previous chat history, or the context above, to respond."
            ),
            verbose=False,
        )

        return chat_engine
