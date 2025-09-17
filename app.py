import sqlite3
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.agents import initialize_agent,Tool
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from sqlalchemy import create_engine
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchResults
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
st.title("🦜 LangChain: Chat with SQL DB")

LOCALDB="USE_LOCALDB"
MYSQL="USE_MYSQL"
prompt=ChatPromptTemplate.from_template(
    """
    You are a MySQL expert.

    If the user asks to CREATE a table, you should NOT attempt to read the schema first. 
    Instead, directly generate the SQL `CREATE TABLE` command with appropriate columns.
    

    If an error occurs that the table already exists, consider renaming the table or asking the user for confirmation.

    If the user query requires reading or updating a table, then you can look at the schema.
     
    If the user query about something that need to webs earched first verfy the schema of asked table or askea ntyhing then according to that schemna web search.
    Web search results:
    {results}

    Previous conversation:
    {prev}

    Answer:
"""
)

search=DuckDuckGoSearchResults(name="search",num_results=10)
radio_opt=["Use SQLLite 3 Database- Student.db","Connect to you MySQL Database"]

selected_opt=st.sidebar.radio(label="Choose the DB which you want to chat",options=radio_opt)

if radio_opt.index(selected_opt)==1:
    db_uri=MYSQL
    mysql_host=st.sidebar.text_input("Provide MySQL Host")
    mysql_user=st.sidebar.text_input("MYSQL User")
    mysql_password=st.sidebar.text_input("MYSQL password",type="password")
    mysql_db=st.sidebar.text_input("MySQL database")
else:
    db_uri=LOCALDB

api_key=st.sidebar.text_input(label="GRoq API Key",type="password")

if not db_uri:
    st.info("Please enter the database information and uri")

if not api_key:
    st.info("Please add the groq api key")
else:
  llm=ChatGroq(groq_api_key=api_key,model_name="gemma2-9b-it",streaming=True)

@st.cache_resource(ttl="2h")
def configure_db(db_uri,mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if db_uri==LOCALDB:
        dbfilepath=(Path(__file__).parent/"student.db").absolute()
        print(dbfilepath)
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri==MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        return SQLDatabase(create_engine(f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))   
    
if db_uri==MYSQL:
    db=configure_db(db_uri,mysql_host,mysql_user,mysql_password,mysql_db)
else:
    db=configure_db(db_uri)

## toolkit
if api_key:
    toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_tools=toolkit.get_tools()

    # agent=create_sql_agent(
    #     llm=llm,
    #     toolkit=toolkit,
    #     verbose=True,
    #     agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
    # )
    # sql_tool=Tool(
    #     name="SQL tool",
    #     func=agent.run,
    #     description="An sql agent which performs crud operations"
    # )
    chain=prompt|llm
    
    def search_web(query: str)->str:
        results=search.run(query)
        return chain.invoke({"results":results,"prev":st.session_state.messages})
    search_tool = Tool(
    name="Web Search",
    func=search_web,
    description="Use this for answering general knowledge or current events questions using web search."
    )  
    tools=sql_tools+[search_tool]
    sql_agent=initialize_agent(
        tools,llm,agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,handle_parsing_errors=True,verbose=True
    )

if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
if st.sidebar.button("🔄 Refresh Database Schema"):
    st.cache_resource.clear()  # Clears all cached resources
    st.rerun()

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query=st.chat_input(placeholder="Ask anything from the database")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)
    
    with st.chat_message("assistant"):
        streamlit_callback=StreamlitCallbackHandler(st.container())
        response=sql_agent.run(user_query,callbacks=[streamlit_callback])
        st.session_state.messages.append({"role":"assistant","content":response})
        st.write(response)
