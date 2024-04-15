import os
import re
import streamlit as st
import json 
from typing import List
# Google sheets as DB
import pandas as pd
from streamlit_gsheets import GSheetsConnection
#############
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.pydantic_v1 import BaseModel, Field
from decouple import config

#parser
class user_detail(BaseModel):
    # user_data: dict = Field(description="The output should only contain a JSON instance that conforms to the JSON schema below. Here is the output schema delimited by triple backticks: ```{'Annual_income': '20000', 'Marital_Status': 'Single', ...}```")
    annual_income: int = Field(description="integer, default: 0")
    marital_status: str = Field(description="single or married, default: NaN")
    cost_of_living: int = Field(description="Integer value, default: 0")
    age: int = Field(description="Integer value, User's age, default: 0")
    

# Input API key here
os.environ['OPEN_API_KEY'] = ''


st.set_page_config(
  page_title="FinX",
  page_icon="🤖",
  layout="wide"
)


user_prompt = st.chat_input()
llm = ChatOpenAI(openai_api_key = config("OPEN_API_KEY"),  temperature=0)  #model="gpt-4",


prompt1 = PromptTemplate(
  input_variables = ["chat_history", "human_input"],
  template="""You are a financial advisor to help user with budgeting plans. 
              Keep all of the currency in INR ₹
              Follow these steps 

              1. Ask user questions to Gather following information
                  a. Annual Income 
                  b. Marital Status 
                  c. Cost of living 
                  d. Age 

              
              2. If user has trouble figuring out cost of living ask general questions and give it a general amount yourself 

              3. Once you have received all of these information generate a budgeting plan for the next 5 years of this person for comfortable retirement plan by age 50 
              chat_history: {chat_history}
              Human: {human_input}


              AI:"""
)

parser = PydanticOutputParser(pydantic_object=user_detail)
output_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)

# for extracting user info
prompt2 = PromptTemplate(
  input_variables = ["chat_history", "human_input"],
  template="""You are a financial advisor to help user with budgeting plans. 
              Keep all of the currency in INR ₹
              Follow these steps 

              If user tries to give information about 
                  a. Annual Income 
                  b. Marital Status 
                  c. Cost of living 
                  d. age 

              all at once or step by step then just output a dictionry of each input and please make sure the money amount is all in numbers and the String starts with capital letter

              
                  Annual Income 
                  Marital Status 
                  Cost of living 
                  Age 


              update keys if user updates any 
            
              only reply with dictionary and nothing else and do not populate it unless the user has provided these informations
              chat_history: {chat_history}
              Human: {human_input} 

              AI:""",
              #parser
              partial_variables={"format_instructions": parser.get_format_instructions()},
)


memory = ConversationBufferMemory(memory_key="chat_history", llm=llm)
llm_chain = LLMChain(
  llm=llm,
  memory=memory,
  prompt=prompt1,
)

## LLM chain 2 used in prompt2
memory2 = ConversationBufferMemory(memory_key="chat_history", llm=llm)
llm_chain_2  = LLMChain(
  llm=llm,
  memory=memory2,
  prompt=prompt2,
  
)


# Fonts and Style
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)


st.title("FinX")

if "messages" not in st.session_state.keys():
  st.session_state.messages = [
    {"role": "assistant", "content": "Hi I am your financial advisor, will you be willing to share a few details with me"}
  ]


for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.write(message["content"])



if user_prompt is not None:
  st.session_state.messages.append({"role": "user", "content": user_prompt})
  with st.chat_message("user"):
    st.write(user_prompt)

def process_data(parsed_output):
   user_data = {
      'annual_income' : parsed_output.annual_income,
      'marital_status': parsed_output.marital_status,
      'cost_of_living': parsed_output.cost_of_living,
      'age': parsed_output.age
   }
   user_data_json = json.dumps(user_data)
   print(user_data)
   print(user_data_json)
   st.session_state.user_info.update(user_data)



if st.session_state.messages[-1]["role"] != "assistant":
  with st.chat_message("assistant"):
    with st.spinner("Loading..."):
      ai_response = llm_chain.predict(human_input=user_prompt)

      st.write(ai_response)

      #for Side bar user info update and JSON format ouput
      ai_dict = llm_chain_2.predict(human_input=user_prompt)

      ai_dict = llm_chain_2.predict(human_input=user_prompt)
      parsed_output = output_parser.parse(ai_dict)
      print("This is Parsed Output:", parsed_output)

      #-------------------------------------------#

      sheet_data = [ {"Annual_Income": parsed_output.annual_income, "Marital_Status": parsed_output.marital_status, 
                "Cost_of_Living": parsed_output.cost_of_living, "Age": parsed_output.age} ]

      #Establishing a Google Sheets connection
      conn = st.connection("gsheets", type=GSheetsConnection)
      #data = conn.read(worksheet="Sheet1")

      up_data = conn.update(worksheet="Sheet1", data=sheet_data)
      del data["Unnamed: 4"]
      up_data = up_data.dropna(how="all")
      st.dataframe(up_data)



    #-------------------------------------------#

      #JSON format and Dictionary format output
      process_data(parsed_output) 

  new_ai_message = {"role": "assistant", "content": ai_response}
  st.session_state.messages.append(new_ai_message)


##############################
  

# Initialize session state for user info if not already set
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}

# Display user info in the sidebar
with st.sidebar:
    st.subheader("User Information")
    if 'user_info' in st.session_state and st.session_state.user_info:
        for key, value in st.session_state.user_info.items():
            st.write(f"{key.capitalize()}: {value}")


