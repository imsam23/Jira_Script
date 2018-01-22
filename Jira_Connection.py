#!/usr/bin/env python
#info for base url for CISOC and SKY JIRA

jiraBaseUrl_xyz = 'http://www.xyz.com/rest/api/'
jiraBaseUrl_abc ='https://www.abc.com/jira/rest/api/'
jiraRestVersion = 'latest'
jiraUrl_cisco = jiraBaseUrl_xyz + jiraRestVersion
jiraUrl_sky=jiraBaseUrl_abc + jiraRestVersion
startAt=0
maxResults=1000
FirstJira='NGDEV-2'


#user credentials info
cert = "../Certificate/certificate.pem"
key_file = "../Certificate/keys.pem"
username = "hip-systems-jira.gen"
password_sky = "blR3NWdYNERH"
password_cisco="amlyYUBjMGRlMDI="
#Filter to query JIRA
projectId='NGDEV'
issuetype='Bug'
