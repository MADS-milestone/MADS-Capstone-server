import requests as req
from dotenv import load_dotenv
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url, text
import sqlalchemy as db
from sqlalchemy_utils import database_exists, create_database, drop_database

from utils_16F import extract_from_json, format_flattened_dict, flatten_dict

load_dotenv()

llm_keys_to_include = [
    "Brief title",
    "National Clinical Identification NCT ID",
    "Lead sponsor",
    "Arms group 0 intervention names",
    "Enrollment count"
]

embedding_keys_to_include = [
    "Brief title",
    "National Clinical Identification NCT ID",
    "Lead sponsor",
    "Arms group 0 intervention names",
    "Enrollment count"
]


class IndexManager:

    def __init__(self, conn_str, table_name, embed_dim):
        self.conn_str = conn_str
        self.table_name = table_name
        self.embed_dim = embed_dim

    def _get_trial(self, nct_id):
        """
        Return: the JSON data for a clinical trial given its NCT ID.
        """
        trial = req.get(f"https://clinicaltrials.gov/api/v2/studies/{nct_id}")
        trial_json = trial.json()
        return trial_json

    def _max_keys(self, documents_list):
        """
        Identifies the document with the maximum number of keys in a list of dictionaries.
        Return: a list of keys from the document with the maximum number of keys.
        """
        max_index, _ = max(enumerate(documents_list), key=lambda x: len(x[1].keys()))
        all_keys = list(documents_list[max_index].keys())
        return all_keys

    def _adjust_metadata_keys(self, all_keys, keys_to_include):
        """
        To adjust the metadata keys used.
        Return: keys to exclude from list of all_keys not in list of keys_to_include.
        """
        keys_to_exclude = [key for key in all_keys if key not in keys_to_include]
        return keys_to_exclude

    def _create_llama_docs(self,
                           documents_list,
                           llm_keys_to_exclude,
                           embedding_keys_to_exclude):
        """
        Converts a list of trial documents into LlamaIndex Document objects.
        """

        llama_documents = []
        for trial in documents_list:
            # apply functions from utils to flatten JSON and create content similar to the example above
            content_text = format_flattened_dict(flatten_dict(trial))

            llama_document = Document(
                id_=trial["National Clinical Identification NCT ID"],
                text=content_text,
                metadata=trial,
                excluded_llm_metadata_keys=llm_keys_to_exclude,  # <== adjust?, TBD
                excluded_embed_metadata_keys=embedding_keys_to_exclude,  # <== adjust?, TBD
                metadata_template="{key}=>{value}",
                text_template="Metadata:\n{metadata_str}\n===========================\nContent: \n{content}"
            )
            llama_documents.append(llama_document)
        return llama_documents

    def _create_nodes(self, llama_documents, embed_model):
        """
        Generates and embeds nodes from Llama documents.
        """
        parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)  # <== adjust from default values
        nodes = parser.get_nodes_from_documents(llama_documents)
        for node in nodes:
            node_embedding = embed_model.get_text_embedding(
                node.get_content(metadata_mode=MetadataMode.EMBED)
            )
            node.embedding = node_embedding
        return nodes

    def load_trials(self, nct_ids: list):

        documents_list = []

        for nct_id in nct_ids:
            trial_json = self._get_trial(nct_id)
            extracted_json = extract_from_json(trial_json)
            documents_list.append(extracted_json)

        all_keys = self._max_keys(documents_list)
        llm_keys_to_exclude = self._adjust_metadata_keys(all_keys, llm_keys_to_include)
        embedding_keys_to_exclude = self._adjust_metadata_keys(all_keys, llm_keys_to_include)

        llama_documents = self._create_llama_docs(documents_list, llm_keys_to_exclude, embedding_keys_to_exclude)
        nodes = self._create_nodes(llama_documents, Settings.embed_model)

        url = make_url(self.conn_str)

        if not database_exists(url):
            create_database(url)

        hybrid_vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name=self.table_name,
            embed_dim=self.embed_dim,  # openai embedding dimension
            hybrid_search=True,
            text_search_config="english"
        )

        hybrid_storage_context = StorageContext.from_defaults(
            vector_store=hybrid_vector_store
        )

        hybrid_index = VectorStoreIndex(
            nodes=nodes,
            storage_context=hybrid_storage_context,
            store_nodes_override=True
        )

        return hybrid_index

    @classmethod
    def delete_index(cls, conn_str, index_table):
        engine = db.create_engine(conn_str)
        with engine.connect() as conn:
            conn.exec_driver_sql(f"truncate table {index_table}")
            conn.commit()
        return True

    @classmethod
    def get_index_length(cls, conn_str, index_table):
        url = make_url(conn_str)
        if not database_exists(url):
            return 0
        engine = db.create_engine(conn_str)
        insp = db.inspect(engine)
        has_table = insp.has_table(index_table)
        if not has_table:
            return 0
        with engine.connect() as conn:
            res = conn.execute(text(f"select count(*) from {index_table}"))
            index_len = res.fetchone()

        return index_len[0]


