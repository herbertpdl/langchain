from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import trim_messages
from langchain_core.runnables import RunnableLambda

load_dotenv()

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that answers with a short joke when possible"),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

llm = ChatOpenAI(model="gpt-5-nano", temperature=0.9)

def prepare_inputs(payload: dict) -> dict:
    raw_history = payload.get("raw_history", [])
    trimmed = trim_messages(
        raw_history,
        token_counter=len,
        max_tokens=2,
        strategy="last",
        start_on="human",
        include_system=True,
        allow_partial=False
    )
    return {"input": payload.get("input"), "history": trimmed}

prepare = RunnableLambda(prepare_inputs)
chain = prepare | prompt | llm

session_store: dict[str, InMemoryChatMessageHistory] = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]

conversational_chain = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="raw_history"
)

config = {"configurable": {"session_id": "demo-session"}}

# Interactions
response1 = conversational_chain.invoke({"input": "Hello, my name is Herbert. reply with 'OK' and do not mention my name"}, config=config)
print("Assistant: ", response1.content)
print("-"*30)

response2 = conversational_chain.invoke({"input": "Tell me a one-sentence fun fact. Do not mention my name again"}, config=config)
print("Assistant: ", response2.content)
print("-"*30)

response3 = conversational_chain.invoke({"input": "What's my name?"}, config=config)
print("Assistant: ", response3.content)
print("-"*30)