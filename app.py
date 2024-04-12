from flask import Flask, request, jsonify
from gen_llm_lib import LocalLLMServerConnection

app = Flask(__name__)


@app.route('/process_input', methods=['POST'])
def process_input():
    if request.method == 'POST':
        user_prompt = request.json.get('user_prompt')

        if user_prompt:
            connection = LocalLLMServerConnection(user_prompt)
            result = connection.process_user_input()
            response = result
            print(response)
            return jsonify({'result': result})
        else:
            return jsonify({'error': 'Invalid input'}), 400


if __name__ == '__main__':
    app.run(debug=True)
