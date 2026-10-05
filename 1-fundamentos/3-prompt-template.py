from langchain_core.prompts import PromptTemplate

template = PromptTemplate(
    input_variables=["name"],
    template="Hi I'm {name}! Tell my a joke with my name!"
)

text = template.format(name="Herbert")
print(text)