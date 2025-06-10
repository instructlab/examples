from flask import Flask, request, Response, jsonify
from werkzeug import exceptions
from qna.qna import MockFactGenerator

import logging

# Globals
app = Flask(__name__)
port_number = 11434
app.logger.setLevel(logging.DEBUG)
fact_generator = MockFactGenerator(app.logger)

def completion_response(content: str, model: str="gpt-3.5") -> dict:
    response = {
        "id": "chatcmpl-2nYZXNHxx1PeK1u8xXcE1Fqr1U6Ve",
        "object": "chat.completion",
        "created": "12345678",
        "model": model,
        "system_fingerprint": "fp_44709d6fcb",
        "choices": [
            {
                "text": content,
                "content": content,
                "index": 0,
                "logprobs": None,
                "finish_reason": "length"
            },
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens":30,
        }
    }

    return response

# Routes
@app.route('/v1/completions', methods=['POST'])
def mock_generate():
    if not request.json or 'prompt' not in request.json:
        issue = "prompt is empty or None"
        app.logger.debug(issue)
        raise exceptions.BadRequest(issue)

    prompt_debug_str = request.json['prompt'][:90] + "..."
    app.logger.debug(f"{request.method} {request.url} {request.json['model']} {prompt_debug_str}")
    if request.json == None:
        raise exceptions.BadRequest("Bad Request: request json empty")
    
    prompt = request.json['prompt']
    
    # handle prompt and generate correct response
    completion = fact_generator.generatePair(prompt)
    if not completion:
        completion = ""

    response = jsonify(completion_response(completion, request.json['model']))
    app.logger.debug(f"response: {response}")
    return response

if __name__ == '__main__':
    app.run(debug=True, port=port_number)
