# res://scenes/api_test_scene.gd (DEBUGGING VERSION)
extends Control

@onready var model_input: LineEdit = $VBoxContainer/ModelInput
@onready var prompt_input: LineEdit = $VBoxContainer/PromptInput
# We don't need references to the other UI for this test.

func _ready() -> void:
	print("--- Debug scene ready. Connecting signals. ---")
	OllamaApi.chat_completion_received.connect(_on_chat_completion_received)
	OllamaApi.text_completion_received.connect(_on_text_completion_received)
	OllamaApi.embedding_received.connect(_on_embedding_received)
	OllamaApi.model_list_received.connect(_on_model_list_received)
	OllamaApi.model_info_received.connect(_on_model_info_received)
	OllamaApi.api_error.connect(_on_api_error)

# --- Button Press Handlers ---
func _on_chat_button_pressed() -> void:
	print("\n>>> 'Chat Completion' button pressed.")
	OllamaApi.request_chat_completion(model_input.text, prompt_input.text)

func _on_text_button_pressed() -> void:
	print("\n>>> 'Text Completion' button pressed.")
	OllamaApi.request_text_completion(model_input.text, prompt_input.text)

func _on_embed_button_pressed() -> void:
	print("\n>>> 'Get Embedding' button pressed.")
	OllamaApi.request_embedding(model_input.text, prompt_input.text)

func _on_list_models_button_pressed() -> void:
	print("\n>>> 'List Models' button pressed.")
	OllamaApi.request_model_list()

func _on_model_info_button_pressed() -> void:
	print("\n>>> 'Get Model Info' button pressed.")
	OllamaApi.request_model_info(model_input.text)

# --- Signal Response Handlers (PRINT ONLY) ---
func _on_chat_completion_received(response_text: String) -> void:
	print("--- SUCCESS: Chat Completion Received ---")
	print(response_text)

func _on_text_completion_received(response_text: String) -> void:
	print("--- SUCCESS: Text Completion Received ---")
	print(response_text)

func _on_embedding_received(embedding_vector: Array) -> void:
	print("--- SUCCESS: Embedding Received ---")
	print("Vector size: %d" % embedding_vector.size())
	print(embedding_vector)

func _on_model_list_received(models_array: Array) -> void:
	print("--- SUCCESS: Model List Received ---")
	print(models_array)

func _on_model_info_received(model_info_dict: Dictionary) -> void:
	print("--- SUCCESS: Model Info Received ---")
	print(model_info_dict)

func _on_api_error(response_code: int, error_message: String) -> void:
	print("--- ERROR: API Error Received ---")
	print("Response Code: ", response_code)
	print("Error Message: ", error_message)
