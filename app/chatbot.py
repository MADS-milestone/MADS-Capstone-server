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
            similarity_top_k=3,  # <== adjust
            #chat_mode="condense_plus_context",
            chat_mode="condense_question",
            vector_store_query_mode="hybrid",
            sparse_top_k=2,
            memory=memory,
            context_prompt=(
                """
                You are a chatbot which is expert in parsing information.
                When asked a question, provide a complete response, concisely.
                """
                "Here are the relevant documents for the context:\n"
                "{context_str}"
                "\nInstruction: Use only the context above or this chat history to respond."
                "If you are unable to find any information related to the query in the context, please say 'Oof, I don't know'."
            ),
            verbose=False,
        )

        return chat_engine
