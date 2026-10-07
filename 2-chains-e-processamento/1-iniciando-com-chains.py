from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

question_template = PromptTemplate(
    input_variables=["name"],
    template="Hi I'm {name}! Tell my a joke with my name!"
)

model = ChatOpenAI(model="gpt-5-mini", temperature=0.5)

chain = question_template | model

result = chain.invoke({"name": "Herbert"})
print(result.content)