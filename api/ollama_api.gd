# res://api/ollama_api.gd (DEBUGGING VERSION)
class_name OllamaAPI
extends Node

# (Signals are the same)
signal chat_completion_received(response_text)
signal text_completion_received(response_text)
signal embedding_received(embedding_vector)
signal model_list_received(models_array)
signal model_info_received(model_info_dict)
signal api_error(response_code, error_message)

var http_request: HTTPRequest
var base_url: String
enum RequestType { CHAT_COMPLETION, TEXT_COMPLETION, EMBEDDING, LIST_MODELS, MODEL_INFO }
var last_request_type: RequestType

func _ready() -> void:
	base_url = ProjectSettings.get_setting("api/ollama_base_url") as String
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_request_completed)

# (Public API functions are the same)
func request_chat_completion(model: String, prompt: String, system_prompt: String = "") -> void:
	var url = "%s/v1/chat/completions" % base_url
	var messages = []
	if not system_prompt.is_empty(): messages.push_back({"role": "system", "content": system_prompt})
	messages.push_back({"role": "user", "content": prompt})
	var body = {"model": model, "messages": messages, "stream": false}
	last_request_type = RequestType.CHAT_COMPLETION
	_make_request(url, HTTPClient.METHOD_POST, body)
func request_text_completion(model: String, prompt: String, max_tokens: int = 100) -> void:
	var url = "%s/v1/completions" % base_url
	var body = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "stream": false}
	last_request_type = RequestType.TEXT_COMPLETION
	_make_request(url, HTTPClient.METHOD_POST, body)
func request_embedding(model: String, text_to_embed: String) -> void:
	var url = "%s/api/embeddings" % base_url
	var body = {"model": model, "prompt": text_to_embed}
	last_request_type = RequestType.EMBEDDING
	_make_request(url, HTTPClient.METHOD_POST, body)
func request_model_list() -> void:
	var url = "%s/v1/models" % base_url
	last_request_type = RequestType.LIST_MODELS
	_make_request(url, HTTPClient.METHOD_GET)
func request_model_info(model: String) -> void:
	var url = "%s/v1/models/%s" % [base_url, model]
	last_request_type = RequestType.MODEL_INFO
	_make_request(url, HTTPClient.METHOD_GET)

# --- Internal Logic with DEBUG PRINTS ---
func _make_request(url: String, method: HTTPClient.Method, body: Dictionary = {}) -> void:
	# ADDED FOR DEBUGGING
	print("--- Making Request ---")
	print("URL: ", url)
	print("METHOD: ", "POST" if method == HTTPClient.METHOD_POST else "GET")
	
	http_request.cancel_request()
	var headers = ["Content-Type: application/json"]
	var body_json_string = ""
	if not body.is_empty():
		body_json_string = JSON.stringify(body)
		# ADDED FOR DEBUGGING
		print("BODY: ", body_json_string)
	
	http_request.request(url, headers, method, body_json_string)

func _on_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var response_body_string = body.get_string_from_utf8()

	# ADDED FOR DEBUGGING - This is the most important print!
	print("--- Request Completed ---")
	print("RESPONSE CODE: ", response_code)
	print("RAW RESPONSE BODY: ", response_body_string)

	if response_code != 200:
		api_error.emit(response_code, response_body_string)
		return

	var json_response = JSON.parse_string(response_body_string)
	if json_response == null:
		var error_msg = "Failed to parse JSON response from Ollama."
		print(error_msg) # ADDED FOR DEBUGGING
		api_error.emit(-1, error_msg)
		return
	
	# ADDED FOR DEBUGGING
	print("PARSED JSON: ", json_response)

	# (The match statement is the same)
	match last_request_type:
		RequestType.CHAT_COMPLETION:
			if json_response.has("choices") and not json_response.choices.is_empty():
				chat_completion_received.emit(json_response.choices[0].message.content)
			else: print("Error: Malformed chat completion response.")
		RequestType.TEXT_COMPLETION:
			if json_response.has("choices") and not json_response.choices.is_empty():
				text_completion_received.emit(json_response.choices[0].text)
			else: print("Error: Malformed text completion response.")
		RequestType.EMBEDDING:
			if json_response.has("embedding"):
				embedding_received.emit(json_response.embedding)
			else: print("Error: Malformed embedding response.")
		RequestType.LIST_MODELS:
			if json_response.has("models"):
				model_list_received.emit(json_response.models)
			else: print("Error: Malformed model list response.")
		RequestType.MODEL_INFO:
			model_info_received.emit(json_response)
