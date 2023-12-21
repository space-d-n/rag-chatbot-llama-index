import logging
import os
from typing import Dict

from configparser import ConfigParser

from flask import Flask, request, jsonify

from transformers import LlamaTokenizer

from llama_index import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    ServiceContext,
    set_global_tokenizer,
)
from llama_index.llms import LlamaCPP
from llama_index.llms.llama_utils import (
    messages_to_prompt,
    completion_to_prompt,
)
from llama_index.indices.base import BaseIndex
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.chat_engine.types import ChatMode
from llama_index.agent import ReActAgent
from llama_index.chat_engine import *

conf = ConfigParser()
conf.read("config.ini")

log_level = logging.DEBUG if conf.getboolean("logging", "debug") else logging.INFO
logging.basicConfig(level=log_level)

context_prompt_file = conf.get("llm", "context_prompt_file")
try:
    with open(context_prompt_file, 'r') as file:
        context_prompt = file.read()
except FileNotFoundError:
    logging.warning('File not found. Using default context prompt.')
    context_prompt = None # by passing None, the default context prompt will be used

logging.info(f"""\n--Context Prompt--
{context_prompt}
--Context Prompt end--
""")

def set_tokenizer(conf: ConfigParser):
    llama_tokenizer = LlamaTokenizer.from_pretrained(
        pretrained_model_name_or_path=conf.get("llm", "model_path_hf"),
        token=conf.get("llm", "api_token_hf"),
    )
    set_global_tokenizer(llama_tokenizer.encode)

# Specifically for web server environment, some issue with FastTokenizers.
# Maybe switch to normal tokenizers. Not a problem for now.
# More context here - https://stackoverflow.com/questions/62691279/how-to-disable-tokenizers-parallelism-true-false-warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"
set_tokenizer(conf)

def init_service_context(conf: ConfigParser) -> ServiceContext:
    # Can be another model, used LlamaCPP since it's designed to run 
    # the LLaMA model using 4-bit integer quantization on a MacBook
    llm = LlamaCPP(
        model_path=conf.get("llm", "model_location"),
        temperature=0,
        max_new_tokens=512,
        # llama2 has a context window of 4096 tokens, recommended to set a little lower
        context_window=3900,
        # kwargs to pass to __call__()
        generate_kwargs={},
        # kwargs to pass to __init__()
        # set to at least 1 to use GPU
        model_kwargs={"n_gpu_layers": 1},
        # transform inputs into Llama2 format with <INST> and <SYS> tags
        messages_to_prompt=messages_to_prompt,
        completion_to_prompt=completion_to_prompt,
        verbose=True
    )

    embed_model = HuggingFaceEmbedding(
        model_name=conf.get("llm", "embedding_model_name")
    )
    return ServiceContext.from_defaults(llm=llm, embed_model=embed_model)


def create_index(conf: ConfigParser, service_context: ServiceContext) -> BaseIndex:
    documents = SimpleDirectoryReader(conf.get("llm", "documents_location"), recursive=True).load_data()
    return VectorStoreIndex.from_documents(documents, service_context=service_context)

# llm context initialization
service_context = init_service_context(conf)
index = create_index(conf, service_context)

app = Flask("llm-chatbot-server")

# chat context for different users
agent_dict: Dict[str, ReActAgent] = {}

@app.route("/prompt", methods=["POST"])
def prompt():
    if not request.is_json:
        return jsonify({"error": "Request must contain context JSON"}), 400

    data = request.get_json()

    message = data.get("message")
    chat_id = data.get("chat_id")

    if chat_id in agent_dict:
        agent: CondensePlusContextChatEngine = agent_dict[chat_id]
    else:
        agent: CondensePlusContextChatEngine = index.as_chat_engine(
            service_context=service_context, 
            context_prompt=context_prompt,
            skip_condense=True,
            chat_mode=ChatMode.CONDENSE_PLUS_CONTEXT, 
            verbose=True
        )
        agent_dict[chat_id] = agent

    chat_response = agent.chat(message.strip())

    return jsonify({"response": chat_response.response.strip()})


if __name__ == "__main__":
    app.run(debug=True)
