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
    def __init__(self):
        self.llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        self.host = 'localhost'
        self.port = '3305'
        self.username = 'root'
        self.password = 'root'
        self.database_schema = 'nasa_space_exploration_database'
        self.mysql_uri = f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_schema}"
        self.db_metadata = MySqlMetaDataLoader(self.host, self.port, self.username, self.password, self.database_schema)
        self.table_names = self.db_metadata.get_table_names()

        self.db = SQLDatabase.from_uri(self.mysql_uri,
                                       include_tables=self.table_names,
                                       sample_rows_in_table_info=2)

    def get_context(self):
        return self.db.get_context()

    def create_query_chain(self):
        return create_sql_query_chain(self.llm, self.db)

    def create_prompt(self):
        context = self.get_context()
        # training_prompts = load_database_prompts(
        #     'C:\\Users\\rahin\source-code\\PycharmProjects\\generative-data-analytics-engine\\project_config'
        #     '\\database_prompt.json')
        training_prompts = load_database_prompts('project_config/database_prompt.json')
        example_prompt = PromptTemplate.from_template("User input: {input}\nSQL query: {query}")
        prompt = FewShotPromptTemplate(
            examples=training_prompts,
            example_prompt=example_prompt,
            prefix="You are a Mysql expert. Given an input question, create a syntactically correct Mysql query to run."
                   "Unless otherwise specified, do not return more than {top_k} rows.\n\nHere is the relevant table "
                   "info: {"
                   "table_info}\n\nBelow are a number of examples of questions and their corresponding SQL queries.",
            suffix="User input: {input}\nSQL query: ",
            input_variables=["input", "top_k", "table_info"],
        )
        return prompt.format(
            input="",
            top_k=5,
            table_info=context["table_info"]
        )

    def generate_sql_query(self, user_prompt):
        chain = self.create_query_chain()
        prompt = self.create_prompt()
        response = chain.invoke(
            {
                "question": user_prompt
            }
        )
        return response

    def process_user_input(self, user_prompt):
        response = self.generate_sql_query(user_prompt)
        return response


if __name__ == "__main__":
    connection = LocalLLMServerConnection()
    user_prompt = ("Create a new table for me named astronaut food list, and create a new table called food info and "
                   "add astronaut_id to that table as a foreign key. Also, attach some insert data.")
    result = connection.process_user_input(user_prompt)
    print(result)
