from config.aid_lib import load_database_prompts
from operator import itemgetter
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import (ChatPromptTemplate,
                                    FewShotChatMessagePromptTemplate)
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_community.embeddings import OllamaEmbeddings


class LocalLLMServerConnection:
    def __init__(self, user_prompt: str, db: SQLDatabase):
        self.llm = Ollama(base_url='http://192.168.1.248:11434', model="mistral_open_orca_7b")
        self.user_prompt = user_prompt
        self.db = db
        self.history = ChatMessageHistory()

    def get_context(self):
        return self.db.get_context()

    def create_query_chain(self, prompt):
        return create_sql_query_chain(self.llm, self.db, prompt)

    def create_prompt(self):
        context = self.get_context()
        training_prompts = load_database_prompts('nasa_database_prompt.json')
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            training_prompts,
            OllamaEmbeddings(base_url='http://192.168.1.248:11434', model="mistral_open_orca_7b"),
            FAISS,
            k=5,
            input_keys=["input"],
        )
        example_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", "{input}\nSQLQuery:"),
                ("ai", "{query}"),
            ]
        )
        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            example_selector=example_selector,
            input_variables=["input", "top_k"],
        )

        system_prompt = (
            "You are a MySQL expert. Given an input question, create a syntactically correct MySQL query to run."
            "Unless otherwise specified. Here is the relevant table info: {table_info}. Below are a number of "
            "examples of questions and their corresponding SQL queries. Also use the {messages} to answer any "
            "followup questions. In case of users wants to know how to answer a followup question or maybe fixing "
            "error, use {messages} to"
            "to Answer the followup question.")

        final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                few_shot_prompt,
                ("human", "{input}"),
            ]
        )
        final_prompt.format(
            input=self.user_prompt,
            top_k=5,
            table_info=context["table_info"],
            messages=self.history.messages
        )

    def generate_sql_query(self):
        generate_query = self.create_query_chain(self.create_prompt())
        chain = (
            RunnablePassthrough.assign(query=generate_query).assign(
                result=itemgetter("query")
            )
        )
        response = chain.invoke({"question": self.user_prompt, "messages": self.history.messages})
        self.history.add_user_message(self.user_prompt)
        self.history.add_ai_message(response['result'])
        return response

    def process_user_input(self):
        response = self.generate_sql_query()
        return response['query']
