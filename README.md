## Overview

I used python version 3.11.7, 3.12 didn't work, not sure about lower versions. Use requirements.txt to download all needed libraries.

This code starts a webserver, which responds to user prompts using llama.cpp model (quantized llama model specifically designed to run on MacBook) and using llama.cpp python bindings.
More about it here:
https://github.com/abetlen/llama-cpp-python - bindings
https://github.com/ggerganov/llama.cpp - llama.cpp


## How to use
Download quantized llama-2-13b (or other .gguf model) from HuggingFace - https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF/blob/main/llama-2-13b-chat.Q4_0.gguf. Maybe to download meta models from HuggingFace you will need to register on Meta website with the same email as on HuggingFace and wait for request confirmation email.

Adjust following in config.ini:
- model_location - path to downloaded model
- api_token_hf - api token from hugging face website

Optionally adjust:
- context_prompt_file - examples in root

Start server with the following command:
python3 chatbot_server.py

Make requests using curl.
Example of curl command to make a request to the server:
curl -X POST -H "Content-Type: application/json" -d '{"message": "<your question>", "chat_id": "1"}' http://127.0.0.1:5000/prompt

Server stores context of the conversation for different chat_id's in-memory in dict.

Final prompt to the model will look like this for a chat with a second question(I took it from chat() method of LlamaCPP class, haven't found a method to extract it to my code, so just put a breakpoint there to see how final prompt looks):
 
\<s> [INST] <<SYS>>\n Provided context:\n\nfile_path: simplex-chat-docs/docs/guide/app-settings.md\n\nHelp & feedback\n\nThis section has information on how to use the app and the links to connect to the team. Please use Send questions and ideas to connect to us via the chat to ask any questions, make any suggestions and report any issues.\n\nfile_path: simplex-chat-docs/docs/guide/managing-data.md\n\nChat Database\n\nTo open your chat database settings:\n\n- Open the app settings.\n- Tap on "Database passphrase & export" button.\n\nYou will be answering questions only based on the provided context.\nYou will be answering user question below. \n<</SYS>>\n\n What is Simplex Chat? [/INST]   Based on the provided context, Simplex Chat is a communication platform that provides secure and private end-to-end encrypted messaging via private connections. It does not use any user identifiers such as emails, phone numbers, usernames, or identity keys to pass messages between users. The platform uses open-source double-ratchet end-to-end encryption protocol and additional encryption layers to ensure the security of messages, and it has no access to user profiles or contacts. \</s>\<s> [INST] How to use it? [/INST]