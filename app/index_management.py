import os

import psycopg2
import requests as req
from dotenv import load_dotenv
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode
from llama_index.vector_stores.postgres import PGVectorStore
from psycopg2.extras import NamedTupleCursor
from sqlalchemy import make_url, text
import sqlalchemy as db
from sqlalchemy_utils import database_exists, create_database, drop_database

from utils import extract_from_json, format_flattened_dict, flatten_dict, init_logging

load_dotenv()
logger = init_logging(__name__)

llm_keys_to_include = [
    "National Clinical Identification NCT ID",
    "Brief title",
    "Condition",
    "Conditions keywords",
    "Lead sponsor",
    "Arms group 0 intervention names",
    "p-value",
    "Statistical Method",
]

embedding_keys_to_include = [
    "National Clinical Identification NCT ID",
    "Brief title",
    "Condition",
    "Conditions keywords",
    "Lead sponsor",
    "Arms group 0 intervention names",
    "p-value",
    "Statistical Method",
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
        parser = SentenceSplitter(chunk_size=8190, chunk_overlap=0)  # <== adjust from default values
        nodes = parser.get_nodes_from_documents(llama_documents)
        for node in nodes:
            node_embedding = embed_model.get_text_embedding(
                node.get_content(metadata_mode=MetadataMode.EMBED)
            )
            node.embedding = node_embedding
        return nodes

    def pull_pfizer_trials(self):
        db_username = os.getenv("AACT_USERNAME")
        db_password = os.getenv("AACT_PASSWORD")

        if not db_username or not db_password:
            raise ValueError("AACT_USERNAME and AACT_PASSWORD must be set in .env")

        conn = psycopg2.connect(
            host="aact-db.ctti-clinicaltrials.org",
            database="aact",
            user=db_username,
            password=db_password,
            port="5432",
            cursor_factory=NamedTupleCursor
        )

        query = """select distinct
                        s.nct_id 
                    FROM
                        studies s
                    LEFT JOIN conditions c ON s.nct_id = c.nct_id
                    LEFT JOIN outcome_analyses oa ON s.nct_id = oa.nct_id
                    WHERE
                        s.study_type IN ('Interventional')
                        AND s.phase IN ('Phase 3')
                        AND s.overall_status = 'Completed'
                        AND oa.p_value IS NOT NULL
                        AND s.source = 'Pfizer'"""

        with conn:
            with conn.cursor() as curs:
                curs.execute(query)
                nct_ids = [rec.nct_id for rec in curs.fetchall()]

        return nct_ids

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

        self.delete_index(self.conn_str, self.table_name)

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
            storage_context=hybrid_storage_context
        )

        return hybrid_index

    @classmethod
    def delete_index(cls, conn_str, index_table):
        engine = db.create_engine(conn_str)
        with engine.connect() as conn:
            conn.exec_driver_sql(f"truncate table data_{index_table}")
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

    def get_most_recent_trial(self, condition):
        db_username = os.getenv("AACT_USERNAME")
        db_password = os.getenv("AACT_PASSWORD")

        if not db_username or not db_password:
            raise ValueError("AACT_USERNAME and AACT_PASSWORD must be set in .env")

        conn = psycopg2.connect(
            host="aact-db.ctti-clinicaltrials.org",
            database="aact",
            user=db_username,
            password=db_password,
            port="5432",
            cursor_factory=NamedTupleCursor
        )

        query = f"""select distinct
                        s.nct_id,
                        s.brief_title
                    FROM
                        studies s
                    LEFT JOIN conditions c ON s.nct_id = c.nct_id
                    LEFT JOIN outcome_analyses oa ON s.nct_id = oa.nct_id
                    WHERE
                        s.study_type IN ('Interventional')
                        AND s.phase IN ('Phase 3')
                        AND s.overall_status = 'Completed'
                        AND oa.p_value IS NOT NULL
                        AND s.source = 'Pfizer'
                        AND (
                            c.downcase_name like '%{condition.lower()}%'
                            OR lower(s.brief_title) like '%{condition.lower()}%'     
                            )
                        ORDER BY s.nct_id DESC
                        --LIMIT 1
                        """

        with conn:
            with conn.cursor() as curs:
                curs.execute(query)
                res = curs.fetchall()

        res_list = []
        for el in res:
            res_list.append({"nct_id": el.nct_id, "brief_title": el.brief_title})

        return res_list

    def set_chatbot_context(self, nct_id):
        pass

