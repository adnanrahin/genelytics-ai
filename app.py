from flask import Flask, request, jsonify
from langchain_community.utilities.sql_database import SQLDatabase

from config import MySqlMetaDataLoader
from gen_llm_lib import LocalLLMServerConnection

app = Flask(__name__)

host = 'localhost'
port = '3305'
username = 'root'
password = 'root'
database_schema = 'nasa_space_exploration_database'
mysql_uri = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_schema}"
db_metadata = MySqlMetaDataLoader(host, port, username, password, database_schema)
db = SQLDatabase.from_uri(mysql_uri,
                          include_tables=db_metadata.get_table_names(),
                          sample_rows_in_table_info=2)


@app.route('/process_input', methods=['POST'])
def process_input():
    if request.method == 'POST':
        user_prompt = request.json.get('user_prompt')

        if user_prompt:
            connection = LocalLLMServerConnection(user_prompt, db)
            result = connection.process_user_input()
            response = result
            print(response)
            return jsonify({'result': result})
        else:
            return jsonify({'error': 'Invalid input'}), 400


if __name__ == '__main__':
    app.run(debug=True)
