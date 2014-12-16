"""
@author: Irina Gvozdeva
@summary: Functions that operate over ZAPI API
"""
import json
import requests
from datetime import datetime, timedelta

jira_server = "https://jira.salsitasoft.com"
execution_status = {"PASS": 1, "FAIL": 2, "WIP": 3, "BLOCKED": 4, "UNEXECUTED": -1}


class ZAPI():
    def __init__(self):
        pass

    def get_projects(self, auth):
        #Get projects from JIRA
        url = "%s/rest/zapi/latest/util/project-list" % jira_server
        r = requests.get(url, auth=auth)
        json_res = json.loads(r.text)
        json_res = json_res["options"]
        return json_res

    def get_project_id(self, project_name, auth):
        #Get project id based on project name
        projects = self.get_projects(auth)
        project_id = None
        for project in projects:
            if project["label"] == project_name:
                project_id = project["value"]
                break
        return project_id

    def get_project_versions(self, project_name, auth):
        #Get project versions, based on project name
        project_id = self.get_project_id(project_name, auth)
        url = "%s/rest/zapi/latest/util/versionBoard-list" % jira_server
        parameters = {"projectId": project_id, "showUnscheduled": "True"}
        r = requests.get(url, auth=auth, params=parameters)
        json_res = json.loads(r.text)
        return json_res

    def get_version_id(self, project_name, version_name, auth):
        #Get version id based on project name and version name
        versions = self.get_project_versions(project_name, auth)
        version_id = None
        for version in versions["unreleasedVersions"]:
            if version["label"] == version_name:
                version_id = version["value"]
                break
        return version_id

    # Cycle api
    def get_project_cycles(self, project_name, version, auth):
        #Get project cycle based on project name and version name
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version, auth)
        url = "%s/rest/zapi/latest/cycle" % jira_server
        parameters = {"projectId": project_id, "versionId": version_id, "offset": 0, "expand": "executionSummaries"}
        r = requests.get(url, auth=auth, params=parameters)
        json_res = json.loads(r.text)
        test_cycle = dict()
        for i in json_res.items():
            if i[0].isdigit():
                test_cycle[i[0]] = list()
                test_cycle[i[0]].append(i[1])
                print(test_cycle)
        return json_res

    def get_cycle_execution_tests(self, cycle_id, auth):
        # Get all executions for cycle with id
        url = "%s/rest/zapi/latest/execution?cycleId=%s" % (jira_server, cycle_id)
        r = requests.get(url, auth=auth)
        json_res = json.loads(r.text)
        executions_list = []
        for i in json_res.items():
            if i[0] == "executions":
                executions_list = i[1]
                break
        for i in range(0, len(executions_list)):
            print executions_list[i]
        return executions_list

    def get_issueid(self, cycle_id, jira_id, auth):
        # Get issue id based on id from Jira
        issues = self.get_cycle_execution_tests(cycle_id, auth)
        issue_id = None
        for issue in issues:
            if issue["issueKey"] == jira_id:
                issue_id = issue["issueId"]
                print(issue_id)
                break
        return issue_id

    def create_new_test_cycle(self, cycle_name, project_name, version_name, auth):
        # Create new test cycle, based on project and version names
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version_name, auth)
        today = datetime.now()
        end_date = today + timedelta(days=30)
        url = jira_server + "/rest/zapi/latest/cycle"
        data = {
            "clonedCycleId": "",
            "name": cycle_name,
            "build": "",
            "environment": "",
            "description": "",
            "startDate": today.strftime("%d/%b/%y"),
            "endDate": end_date.strftime("%d/%b/%y"),
            "projectId": project_id,
            "versionId": version_id
        }
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        json_res = json.loads(r.text)
        cycle_id = json_res["id"]
        return cycle_id

    def copy_test_cycle(self, cycle_id, cycle_name, project_name, version_name, auth):
        #Copy existing test cycle -didn't use it yet
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version_name, auth)
        today = datetime.now()
        end_date = today + timedelta(days=30)
        url = jira_server + "/rest/zapi/latest/cycle"
        data = {
            "clonedCycleId": cycle_id,
            "name": cycle_name,
            "build": "",
            "environment": "",
            "description": "",
            "startDate": today.strftime("%d/%b/%y"),
            "endDate": end_date.strftime("%d/%b/%y"),
            "projectId": project_id,
            "versionId": version_id
        }
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        json_res = json.loads(r.text)
        cycle_id = json_res["id"]
        return cycle_id

    def delete_test_cycle(self, cycle_id, auth):
        #Delete existing test cycle use it's id
        url = "%s/rest/zapi/latest/cycle/%s" % (jira_server, cycle_id)
        r = requests.get(url, auth=auth)
        json_res = json.loads(r.text)
        if "Error" in json_res.keys():
            return None
        else:
            url = "%s/rest/zapi/latest/cycle/%s" % (jira_server, cycle_id)
            r = requests.delete(url, auth=auth)
            json_res = json.loads(r.text)
            print(json_res)
            return json_res

    #Execution API
    def add_new_execution(self, project_name, version_name, cycle_id, issue_id, auth):
        # Add new execution to cycle
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version_name, auth)
        url = "%s/rest/zapi/latest/execution" % jira_server
        data = {
            "issueId": issue_id,
            "versionId": version_id,
            "cycleId": cycle_id,
            "projectId": project_id
        }
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        json_res = json.loads(r.text)
        print json_res
        return json_res.keys()[0]

    def add_tests_to_cycle(self, issue_keys, project_name, version_name, cycle_id, auth):
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version_name, auth)
        url = "%s/rest/zapi/latest/execution/addTestsToCycle" % jira_server
        data = {
            "issues": issue_keys,
            "versionId": version_id,
            "cycleId": cycle_id,
            "projectId": project_id,
            "method": "1"
        }
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        print(r.text)
        json_res = json.loads(r.text)
        return json_res

    def get_execution_id(self, execution_id, auth):
        url = jira_server + "/rest/zapi/latest/execution/%s" % execution_id
        r = requests.get(url, auth=auth)
        json_res = json.loads(r.text)
        return json_res

    def get_execution_test(self, issue_id, auth):
        # Get all executions for issue_id
        url = "%s/rest/zapi/latest/execution/" % jira_server
        parameters = {
            "issueId": issue_id}
        r = requests.get(url, auth=auth, params=parameters)
        json_res = json.loads(r.text)
        return json_res

    def update_execution_status(self, execution_id, status, auth):
        #Update execution status
        url = "%s/rest/zapi/latest/execution/%s/quickExecute" % (jira_server, execution_id)
        data = {'status': execution_status[status]}
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        if r.status_code != 200:
            return None
        else:
            return "Success"
