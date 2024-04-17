from flask import Flask, request, jsonify, render_template
from config import DataBaseConnectionManager
from gen_llm_lib import LocalLLMServerConnection

app = Flask(__name__)

db_connection = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/user_prompt.html')
def user_prompt():
    return render_template('user_prompt.html')


@app.route('/set_db_config', methods=['POST'])
def set_db_config():
    global db_connection

    try:
        data = request.json
        db_config = data.get('db_config')

        if not db_config:
            raise ValueError("Missing 'db_config' data in request body.")

        db_metadata = DataBaseConnectionManager(**db_config)
        db_connection = db_metadata.get_sql_data_base()

        print(db_metadata.get_table_names())

        return jsonify({'message': 'Database configuration set successfully.'})

    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/user_prompt', methods=['POST'])
def process_input():
    global db_connection
    if db_connection is None:
        return jsonify({'error': 'Database connection not established'}), 500

    if request.method == 'POST':
        user_prompt = request.json.get('user_prompt')

        if user_prompt:
            connection = LocalLLMServerConnection(user_prompt, db_connection)
            result = connection.process_user_input()
            response = result
            print(response)
            return jsonify({'result': result})
        else:
            return jsonify({'error': 'Invalid input'}), 400


if __name__ == '__main__':
    app.run(debug=True)
