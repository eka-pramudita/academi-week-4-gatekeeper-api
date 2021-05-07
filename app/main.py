from flask import Flask, jsonify, request
from app.validation import validate_message

app = Flask(__name__)


@app.route("/")
def index() -> str:
    # transform a dict into an application/json response 
    return jsonify({"message": "It Works"})

@app.route("/message", methods=['POST'])
def message() -> str:
    errors = validate_message(request)
    if errors is not None:
        print(errors)
    response = {"error": errors}
    return jsonify(response)

        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)