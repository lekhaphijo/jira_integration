from jira import JIRA
import pymongo
import json
import app.config as cfg

def pull_jira_issue(jira_user, project_key):
    mongo_url = cfg.mongo_url
    mongo_db_name = cfg.mongo_db_name
    mongo_collection_name = cfg.mongo_collection_name
    jira_url = cfg.jira_url
    jira_api_token = cfg.jira_api_token

    jira = JIRA(jira_url, basic_auth=(jira_user, jira_api_token), options={'server': jira_url, 'verify': False})
    mongo_client = pymongo.MongoClient(mongo_url)
    mongo_db = mongo_client[mongo_db_name]
    mongo_collection = mongo_db[mongo_collection_name]
    mongo_collection.drop()
    mongo_collection = mongo_db[mongo_collection_name]
    project_key = project_key
    issues = jira.search_issues(f'project={project_key}')

    # Iterate over each issue
    for issue in issues:
        issue_comments = []
        for comment in issue.fields.comment.comments:
            issue_comments.append({
                "Author": comment.author.displayName,
                "Created": comment.created,
                "Comment": comment.body
            })

        # Check if the issue already exists in the database
        existing_issue = mongo_collection.find_one({"Issue Key": issue.key})

        if existing_issue:
            # Check for new comments
            existing_comments = existing_issue.get("Comments", [])
            existing_comment_bodies = [c['Comment'] for c in existing_comments]
            new_comments = [comment for comment in issue_comments if comment['Comment'] not in existing_comment_bodies]

            if new_comments:
                # Append new comments to the existing issue
                mongo_collection.update_one(
                    {"_id": existing_issue['_id']},
                    {"\$push": {"Comments": {"\$each": new_comments}}}
                )
                print(f"New comments added to issue {issue.key}.")
            else:
                print(f"No new comments to add for issue {issue.key}.")


        # if existing_issue:
        #     # Check for new comments
        #     existing_comments = existing_issue.get("Comments", [])
        #     new_comments = [comment for comment in issue_comments if comment not in existing_comments]

        #     if new_comments:
        #         # Append new comments to the existing issue
        #         mongo_collection.update_one({"_id": existing_issue['_id']}, {"\$push": {"Comments": {"\$each": new_comments}}})
        #         print(f"New comments added to issue {issue.key}.")
        #     else:
        #         print(f"No new comments to add for issue {issue.key}.")

        else:
            # Insert new issue
            issue_data = {
                "Issue Key": issue.key,
                "Summary": issue.fields.summary,
                "Description": issue.fields.description,
                "Status": issue.fields.status.name,
                "Priority": issue.fields.priority.name,
                "Created Date": issue.fields.created,
                "Due Date": issue.fields.duedate,
                "Assignee": issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                "Comments": issue_comments
            }
            mongo_collection.insert_one(issue_data)
            print(f"Issue {issue.key} inserted.")

    # Close the MongoDB connection
    mongo_client.close()
    return "data pulled successfully"


