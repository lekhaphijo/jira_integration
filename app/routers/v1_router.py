from fastapi import APIRouter,Depends, HTTPException, status, Query
from fastapi import File, UploadFile, Form,HTTPException, status, Response
from app.utilities import synechron_logger
from fastapi.responses import FileResponse
from app.routers import datamodels
from pathlib import Path
import app.config as cfg
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from typing import List
import json
from app.services.jira_issues import pull_jira_issue
from app.services.get_jira_answer import get_answer



logger = synechron_logger.SyneLogger(
    synechron_logger.get_logger(__name__), {"model_inference": "v1"}
)
router = APIRouter(
    tags=["Inference"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def health_check():
    """Check the health of services
    author: Rajesh
    Returns:
        [json]: json object with a status code 200 if everything is working fine else 400.
    """
    return {"message": "Status = Healthy"}

@router.post("/pull_data_from_jira")
def pull_data(input: datamodels.JiraIssues):
    jira_user_email = input.jira_user_email
    project_key = input.project_key
    return pull_jira_issue(jira_user_email,project_key)

@router.post("/get_answer")
def pull_data(input: datamodels.GetAnswer):
    que = input.que
    return get_answer(que)



