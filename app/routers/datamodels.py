from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from fastapi import FastAPI, File, UploadFile, Form

class JiraIssues(BaseModel):
    jira_user_email: Optional[str] = Field(None,
                                        example="datascienceexpert39@gmail.com")

    project_key: Optional[str] = Field(None,
                                        example="innovation")


