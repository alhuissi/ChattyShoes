import os
import logging
logging.basicConfig(level=logging.INFO)
import urllib
import google.auth.transport.requests
import google.oauth2.id_token
import json
import openai
import firebase_admin
import functions_framework
from firebase_admin import firestore
from flask import Flask, make_response, jsonify
import tiktoken

from prompting import SYSTEM_PROMPT

# Get the project ID from the environment variables
PROJECT_ID = os.environ.get('PROJECT_ID')
# Get the OpenAI API key from the environment variables
API_KEY = os.environ.get('OPENAI_KEY')
COMMANDS_ENDPOINT = os.environ.get('COMMAND_PROCESSOR_URL')
# Initialize the Firebase app
APP = firebase_admin.initialize_app()
# Set the OpenAI API key
openai.api_key = API_KEY

app = Flask(__name__)

def count_tokens(text, model):
    """
    This function counts the number of tokens in a text.
    Parameters:
        text: The text to count the tokens of.
        model: The model to use for tokenization.
    Returns:
        The number of tokens in the text."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def generate_answer(conversation_info, message):
    """
    This function will continue the conversation.
    Parameters:
        conversation_info: The information of the conversation
        message: The message to append
    """
    logging.info("Generating answer")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in conversation_info["messages"]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    # Limit the conversation history to a certain number of tokens
    max_context_length = 3500  # Adjust this value based on your desired context length
    current_context_length = sum([count_tokens(msg["content"], conversation_info["model_codename"]) for msg in messages])

    while current_context_length > max_context_length:
        removed_message = messages.pop(1)  # Remove the earliest non-system message
        current_context_length -= count_tokens(removed_message["content"], conversation_info["model_codename"])

    full_prompt = {
        "model": conversation_info["model_codename"],
        "messages": messages
    }
    response = openai.ChatCompletion.create(**full_prompt)
    return response["choices"][0]["message"]["content"]

def _save_message(message, role, author, conversation_id):
    """
    This function saves the message in the conversation.
    Parameters:
        message: The message to be saved.
        role: The role of the sender (either "user" or "assistant").
        conversation_id: The ID of the conversation.
    """
    message_info = {"role": role, "author": author, "content": message}
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection('conversations').document(conversation_id)
    doc = doc_ref.get()
    if not doc.exists:
        logging.error("Conversation not found")
        raise Exception("Conversation not found")
    conversation_info = doc.to_dict()
    conversation_info["messages"].append(message_info)
    doc_ref.update(conversation_info)

def _get_conversation_info(conversation_id):
    """
    This function retrieves the information of a conversation from Firestore.
    Parameters:
        conversation_id: The ID of the conversation to retrieve.
    Returns:
        A dictionary representing the conversation information.
    """
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection('conversations').document(conversation_id)
    doc = doc_ref.get()
    if not doc.exists:
        logging.error("Conversation not found")
        raise Exception("Conversation not found")
    return doc.to_dict()

def _make_authorized_post_request(endpoint, payload):
    """
    make_authorized_get_request makes a POST request to the specified HTTP endpoint
    by authenticating with the ID token obtained from the google-auth client library
    using the specified audience value.
    """

    req = urllib.request.Request(endpoint)

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, endpoint)


    req.data=payload
    req.add_header("Authorization", f"Bearer {id_token}")
    req.add_header("Content-Type", "application/json")
    response = urllib.request.urlopen(req)
    return json.load(response)

def _execute_command(message, conversation_id):
    """
    This function executes a command and returns the response message.
    Parameters:
        message: The command message to be executed.
        conversation_info: The information of the conversation.
    Returns:
        A dictionary representing the response message of the command.
    """
    # Extract the command and its arguments
    command = message.split("#c#")[1]
    parts = command.split("#|#")
    command = parts[0]
    args = {"conversationId": conversation_id}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            args[key] = value
    # Call the command handling function and return its response
    response_text = _make_authorized_post_request(COMMANDS_ENDPOINT, 
                                                  json.dumps(args).encode("utf-8"))["responseMessage"]
    # Return the response message
    return response_text

def _return_response(message, conversation_id):
    """
    This function returns a response message.
    Parameters:
        message: The message to be returned.
        role: The role of the sender (either "user" or "assistant").
    Returns:
        A Flask response object.
    """
    if conversation_id != "temp":
        _save_message(message, "assistant", "assistant", conversation_id)
    response = {
                    "author": "assistant",
                    "conversationId": conversation_id,
                    "role": "assistant",
                    "message": message
                }
    response = jsonify(response)
    response.status_code = 200
    response.headers.set('Access-Control-Allow-Origin', '*')  # Adjust this to allow specific origins
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.set('Content-Type', "application/json")
    return response

def _is_command(message):
    return "#c#" in message

def _conversational_bot(event):
    logging.info("Processing event {}".format(event))
    if not "role" in event.keys():
        event["role"] = "user"
    if event["role"] == "user":
        message = str(event["message"])
        conversation_id = str(event["conversationId"])
        user_id = str(event["author"])
        # Get the conversation information
        if conversation_id != "temp":
            try:
                conversation_info = _get_conversation_info(conversation_id)
            except:
                response = {"error": "Error fetching conversation"}
                return Flask.response_class(json.dumps(response), status=400, mimetype="application/json")
            # Check if the user is allowed to continue the conversation
            if user_id not in [conversation_info["user"], "command-executor"]:
                logging.error("User not allowed to continue conversation")
                response = {"error": "User not allowed to continue conversation"}
                return Flask.response_class(json.dumps(response), status=401, mimetype="application/json")
            # Save the user message
            _save_message(message, "user", user_id, conversation_id)
        # Generate the LLM response
        llm_response = generate_answer(conversation_info, message)
        # Check if the LLM response is a command
        if _is_command(llm_response):
            # Save the LLM response
            if conversation_id != "temp":
                _save_message(llm_response, "assistant", "assistant", conversation_id)
            # Execute the command and restart the process with the response as user message
            response = _execute_command(llm_response, conversation_id)
            new_event = {
                "author": "command-executor",
                "conversationId": conversation_id,
                "role": "user",
                "message": response
            }
            return _conversational_bot(new_event)
        else:
            # Return the LLM response
            return _return_response(llm_response, conversation_id)
    else:
        logging.error("Only user messages are allowed")
        response = {"error": "Only user messages are allowed"}
        return Flask.response_class(json.dumps(response), status=400, mimetype="application/json")


@functions_framework.http
def conversational_bot(request):
    if request.method == 'OPTIONS':
        logging.info("Received options request")
        # Preflight request. Reply successfully:
        response = make_response()
        response.headers.set('Access-Control-Allow-Origin', '*')  # Adjust this to allow specific origins
        response.headers.set('Access-Control-Allow-Methods', 'GET, POST')
        response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.set('Access-Control-Max-Age', '3600')
        return response
    logging.info("Received other request")
    event = request.get_json()
    logging.info(event)
    return _conversational_bot(event)
