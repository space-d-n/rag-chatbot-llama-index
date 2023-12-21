Example of curl to make request to the server:
curl -X POST -H "Content-Type: application/json" -d '{"message": "<your question>", "chat_id": "1"}' http://127.0.0.1:5000/prompt

Server stores context of the conversation for different chat_id's in-memory in dict.
