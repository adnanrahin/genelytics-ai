from langchain_community.utilities import SQLDatabase
from langchain_community.llms import OpenAI

from config.aid_lib import load_database_prompts
from config.mysql import MySqlMetaDataLoader
from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.prompt import SQL_PROMPTS
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate


class LocalLLMServerConnection:
    def __init__(self, user_prompt: str, db: SQLDatabase):
        self.llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        self.user_prompt = user_prompt
        self.db = db

    def get_context(self):
        return self.db.get_context()

    def create_query_chain(self):
        return create_sql_query_chain(self.llm, self.db)

    def create_prompt(self):
        context = self.get_context()
        training_prompts = load_database_prompts('project_config/database_prompt.json')
        example_prompt = PromptTemplate.from_template("User input: {input}\nSQL query: {query}")
        prompt = FewShotPromptTemplate(
            examples=training_prompts,
            example_prompt=example_prompt,
            prefix="You are a Mysql expert. Given an input question, create a syntactically correct Mysql query to run."
                   "Unless otherwise specified, do not return more than {top_k} rows.\n\nHere is the relevant "
                   "table info: {table_info}\n\nBelow are a number of examples of questions and their corresponding "
                   "SQL queries.",
            suffix="User input: {input}\nSQL query: ",
            input_variables=["input", "top_k", "table_info"],
        )
        return prompt.format(
            input=self.user_prompt,
            top_k=5,
            table_info=context["table_info"]
        )

    def generate_sql_query(self):
        chain = self.create_query_chain()
        prompt = self.create_prompt()
        response = chain.invoke(
            {
                "question": self.user_prompt
            }
        )
        return response

    def process_user_input(self):
        response = self.generate_sql_query()
        return response
