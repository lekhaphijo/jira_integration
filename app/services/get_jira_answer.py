from jira import JIRA
import pymongo
import json
import openai
import app.config as cfg
# Warning control
import warnings
warnings.filterwarnings('ignore')
import os
from utils import get_openai_api_key, get_serper_api_key
from crewai import Agent, Task, Crew
openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o" #'gpt-3.5-turbo'
os.environ["SERPER_API_KEY"] = get_serper_api_key()
os.environ['OPENAI_API_KEY'] = cfg.OPENAI_API_KEY




os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
from crewai_tools import ScrapeWebsiteTool, SerperDevTool, DirectoryReadTool, FileReadTool
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()
from crewai_tools import BaseTool
import json
from bson import ObjectId
from langchain_community.document_loaders.mongodb import MongodbLoader
# from langchain.chat_models import ChatOpenAI
# from langchain.agents import create_json_agent
from langchain.agents.agent_toolkits import JsonToolkit
from langchain.tools.json.tool import  JsonSpec
import json


class ProjectManagementTool(BaseTool):
    name: str = "Project Management Tool Analysis"
    description: str = ("Analyzes the questation of given text "
                        "fetch the data from the Mongo DB and and try to answer the given questation based of the Mongo DB result and strictly do not add any new things by own")

    def get_data(self):
        loader = MongodbLoader(
            connection_string=cfg.mongo_url,
            db_name=cfg.mongo_db_name,
            collection_name=cfg.mongo_collection_name,
        )
        docs = loader.load()
        json_data_list = {"dummy": []}

        # Assume 'docs' is a list of objects that contain the 'page_content' attribute
        for doc in docs:
            data = doc.page_content.replace("'", '"')
            # Convert ObjectId to string and None to null
            data = data.replace('ObjectId(', '').replace(')', '').replace('None', 'null')

            # Convert the string to a JSON object
            try:
                data_json = json.loads(data)
                json_data_list['dummy'].append(data_json)  # Append the dictionary to the list
            except json.JSONDecodeError as e:
                print(f"An error occurred: {e}")

        # Write the list of JSON objects to a file
        # with open('output3.json', 'w', encoding='utf-8') as f:
        #     json.dump(json_data_list, f, ensure_ascii=False, indent=4)
        return json_data_list

    def _run(self, text: str) -> str:
        data = self.get_data()
        # json_data_list = self.get_data()
        # spec=JsonSpec(dict_=json_data_list,max_value_length=4000)
        # json_tool=JsonToolkit(spec=spec)
        return data


def get_data():
    loader = MongodbLoader(
        connection_string=cfg.mongo_url,
        db_name=cfg.mongo_db_name,
        collection_name=cfg.mongo_collection_name,
    )
    docs = loader.load()
    json_data_list = {"dummy": []}

    # Assume 'docs' is a list of objects that contain the 'page_content' attribute
    for doc in docs:
        data = doc.page_content.replace("'", '"')
        # Convert ObjectId to string and None to null
        data = data.replace('ObjectId(', '').replace(')', '').replace('None', 'null')

        # Convert the string to a JSON object
        try:
            data_json = json.loads(data)
            json_data_list['dummy'].append(data_json)  # Append the dictionary to the list
        except json.JSONDecodeError as e:
            print(f"An error occurred: {e}")

    # Write the list of JSON objects to a file
    with open(f'{cfg.BASE_DIR}/app/resources/instructions/output.json', 'w', encoding='utf-8') as f:
        json.dump(json_data_list, f, ensure_ascii=False, indent=4)
    return json_data_list


def get_answer(que):
    json_data_list = get_data()

    directory_read_tool = DirectoryReadTool(directory=f'{cfg.BASE_DIR}/app/resources/instructions/output.json')
    file_read_tool = FileReadTool()
    search_tool = SerperDevTool()
    project_manager_agent = Agent(
        role="Project Manager",
        goal="Monitor and analyze jira issues"
             "to identify which ticket is has been assigned whome complexity of the tasks",
        backstory="Specializing in Project Management, this agent "
                  "uses statistical modeling and machine learning "
                  "to provide crucial insights. With a knack for data, "
                  "the Poject Manager Agent is the cornerstone for "
                  "informing issues and comments decisions.",
        verbose=True,
        allow_delegation=True,
        tools=[directory_read_tool, file_read_tool]
    )
    # Task for Data Analyst Agent: Analyze Market Data
    project_management_task = Task(
        description=(
            "Continuously monitor and analyze jira issues"
            "and try to analyse the {questation} find out the relevent answer from jira issues json data"
            "Use generative model to "
            "prepare the right answer"
        ),
        expected_output=(
            "give the relevent answer if you know"
            "otherwise just say I don't know the answer of your questation {questation}."
        ),
        agent=project_manager_agent,
    )

    from crewai import Crew, Process
    from langchain_openai import ChatOpenAI

    # Define the crew with agents and tasks
    project_manager_crew = Crew(
        agents=[project_manager_agent],

        tasks=[project_management_task],

        manager_llm=ChatOpenAI(model= "gpt-4o", #"gpt-3.5-turbo",
                               temperature=0.7),
        # process=Process.hierarchical,
        verbose=True,
        memory=True

    )
    inputs = {
        "questation": que
    }
    result = project_manager_crew.kickoff(inputs=inputs)

    return {"data":result}


