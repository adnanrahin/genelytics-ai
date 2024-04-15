from flask import Flask, request, jsonify
from config import DataBaseConnectionManager
from gen_llm_lib import LocalLLMServerConnection

app = Flask(__name__)

db_metadata = DataBaseConnectionManager(db_type='mysql', host='localhost', port='3305', username='root',
                                        password='root', database_schema='nasa_space_exploration_database')
db = db_metadata.get_sql_data_base()


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
