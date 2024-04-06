import os
import re
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from decouple import config

#And greet the user thanking for using the service after the budget plan is served. You are a finance advisor AI agent and your aim is to ask questions from user to develop a budgeting plan, 
              # Question user in a consultant tone and get only the details of age, marital status, annual income, cost of living and devise
              # a budgeting plan after the information is retrieved. And make a planning for monthly budget.

os.environ['OPENAI_API_KEY'] = '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'


def extract_user_info(prompt1):
    user_info = {}

    print(prompt1)
    # Extract annual income
    income_match = re.search(r'annual_income: (\d+)', prompt1, re.IGNORECASE)
    if income_match:
        user_info['annual_income'] = int(income_match.group(1))
  
    #Extracting Martal Status 
    marital_status_match = re.search(r'marital_status: (\w+)', prompt1, re.IGNORECASE)
    if marital_status_match:
        user_info['marital_status'] = marital_status_match.group(1)
    
    
    # Extract cost of living
    cost_of_living_match = re.search(r'cost_of_living: (\d+)', prompt1, re.IGNORECASE)
    if cost_of_living_match:
        user_info['cost_of_living'] = int(cost_of_living_match.group(1))
    
    # Extract age
    age_match = re.search(r'age: (\d+)', prompt1, re.IGNORECASE)
    if age_match:
        user_info['age'] = int(age_match.group(1))


    return user_info


prompt1 = PromptTemplate(
  input_variables = ["chat_history", "question"],
  template="""You are a financial advisor to help user with budgeting plans. 
              Keep all of the currency in INR ₹
              Follow these steps 

              1. Ask user questions to Gather following information
                  a. Annual Income 
                  b. Marital status 
                  c. Cost of living 
                  d. age  

              2. If user has trouble figuring out cost of living ask general questions and give it a general amount yourself 

              3. Once you have recieved all of these informations generate a budgeting plan for the next 5 years of this person for comfortable retirement plan by age 50 
              chat_history: {chat_history}
              Human: {question} 

              AI:"""
)

prompt2 = PromptTemplate(
  input_variables = ["chat_history", "question"],
  template="""You are a financial advisor to help user with budgeting plans. 
              Keep all of the currency in INR ₹
              Follow these steps 

              If user tries to give information about 
                  a. Annual Income 
                  b. Marital status 
                  c. Cost of living 
                  d. age 

              all at once or step by step then just output a dictionry 
              
                annual_income: 
                marital_status:
                cost_of_living:
                age:


              update keys if user updates any 

              only reply with dictionary and nothing else 
              chat_history: {chat_history}
              Human: {question} 

              AI:"""
)

llm = ChatOpenAI(openai_api_key = config("OPENAI_API_KEY"))
memory = ConversationBufferMemory(memory_key="chat_history", k=50)
memory2 = ConversationBufferMemory(memory_key="chat_history", k=50)
llm_chain = LLMChain(
  llm=llm,
  memory=memory,
  prompt=prompt1,
  
)

llm_chain_2  = LLMChain(
  llm=llm,
  memory=memory2,
  prompt=prompt2,
  
)

st.set_page_config(
  page_title="Finance Planning Advice Bot",
  page_icon="🤖",
  layout="wide"
)

st.title("Finance Planning Advice Bot")

if "messages" not in st.session_state.keys():
  st.session_state.messages = [
    {"role": "assistant", "content": "Hi I am your financial advisor, will you be willing to share a few details with me"}
  ]


for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.write(message["content"])


user_prompt = st.chat_input()

if user_prompt is not None:
  st.session_state.messages.append({"role": "user", "content": user_prompt})
  with st.chat_message("user"):
    st.write(user_prompt)

if st.session_state.messages[-1]["role"] != "assistant":
  with st.chat_message("assistant"):
    with st.spinner("Loading..."):
      ai_response = llm_chain.predict(question=user_prompt)
      ai_dict = llm_chain_2.predict(question=user_prompt)

      extracted_info = extract_user_info(ai_dict)
      st.session_state.user_info.update(extracted_info)
      
      st.write(ai_response)
  new_ai_message = {"role": "assistant", "content": ai_response}
  st.session_state.messages.append(new_ai_message)


########################  




# Extracting User info on the sidebar 

# Initialize session state for user info if not already set
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}

# Function to extract user information from the prompt


# Collect user prompt from atop
# user_prompt = st.chat_input()


# Extract and store user information in session state
if user_prompt:
    extracted_info = extract_user_info(user_prompt)
    st.session_state.user_info.update(extracted_info)

# if ai_dict: 
    
# Display user info in the sidebar
with st.sidebar:
    st.subheader("User Information")
    if 'user_info' in st.session_state and st.session_state.user_info:
        for key, value in st.session_state.user_info.items():
            st.write(f"{key.capitalize()}: {value}")
