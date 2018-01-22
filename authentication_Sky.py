#!/usr/bin/env python
import requests
import json
from Jira_Connection import *
import base64
import sys
import logging

logger = logging.getLogger('QUERY')

session=None

#To authenticate the BSKYB server and get the data in JSON format from the server
def authenticateGetData_sky(key):
    url = jiraUrl_sky + '/search?startAt=' + str(startAt) + '&maxResults=' + str(maxResults) + '&jql=project=' + str(projectId) + ' and resolution=Unresolved and issuetype=' + str(issuetype) + ' and Key>' + str(key) + ' ORDER BY key ASC'
    logger.debug(url)
    global session
    with requests.session() as session:
        session.cert=(cert,key_file)
        session.auth=(username,base64.urlsafe_b64decode(password_sky))
        response=session.get(url)
        logger.info("server responded with status :" + str(response.status_code))

    if response.status_code == 200:
        json_data = response.json()
        return json_data['issues'],json_data['total']
    else:
        logger.error("The JIRA server failed to reply correctly (HTTP status): " + str(response.status_code))
        exit(1)

# To Authenticate the CISCO server and return the seesion
def authenticate():
    session=requests.session()
    session.auth=(username,base64.urlsafe_b64decode(password_cisco))
    return session


def getAttachment(key):
    """Get the attachmed file Name and Link for the particular Jira(Key) if attachment is present.
    Attachment is not present in the field so need to parse the particula Jira to get the attachment"""
    url=jiraBaseUrl_sky+'2/issue/'+key+'/?fields=attachment'
    fileName_link=""
    global session
    response=session.get(url)
    logger.info("server responded with status :" + str(response.status_code))
    if response.status_code == 200:
        json_data = response.json()
        if len(json_data['fields']['attachment'])==0:
            pass
        else:
            for count in range(len(json_data['fields']['attachment'])):
                fileName=json_data['fields']['attachment'][count]['filename']
                url=json_data['fields']['attachment'][count]['content']
                fileName_link = fileName_link + '\n' +"{0:50}  {1}".format(fileName,url)

        fileName_link="\n\n\nAttachments from the SKY JIRA-----------------------------------------------------\n"+fileName_link
        return fileName_link

    else:
        logger.error("The JIRA server failed to reply correctly (HTTP status): " + str(response.status_code))


def custom_field():
    url=jiraBaseUrl_sky+"2/issue/createmeta?projectKeys="+projectId+"&issuetypeNames=Bug&expand=projects.issuetypes.fields"
    global session
    pattern='customfield_'
    dict_of_customfiels=dict()
    response=session.get(url)
    if response.status_code==200:
        data= response.json()
        custom_list=data['projects'][0]['issuetypes'][0]['fields']
        for cf in custom_list:
            if pattern in cf:
                dict_of_customfiels[cf]=custom_list[cf]['name']
        return dict_of_customfiels
    else:
        logger.error("The JIRA server failed to reply correctly (HTTP status): " + str(response.status_code))

def sky_hist_total(key):
    global session
    url = jiraBaseUrl_sky + '2/issue/' + str(key) + '/?expand=changelog'
    response=session.get(url)
    if response.status_code==200:
        json_data=response.json()
        total = json_data['changelog']['total']
        return total
    else:
        response.raise_for_status()


def history(key,prev_total_label=None):
    url=jiraBaseUrl_sky+'2/issue/'+str(key)+'/?expand=changelog'
    global session
    dict_with_all_valued=dict()
    dict_updated = dict()
    attachment=''
    logging.info("INSIDE HISTORY")

    response=session.get(url)
    if response.status_code==200:
        json_data=response.json()
        total=json_data['changelog']['total']
        while (total-1)>=(prev_total_label):
            items= json_data['changelog']['histories'][prev_total_label]['items']
            if len(json_data['changelog']['histories'][prev_total_label]['items'])>0:
                for item in items:
                    if item['field']:
                        key=item['field']
                        if item['from']:
                            if item['to']:
                                key=key+'_'+item['to']
                            else:
                                key=key+'_'+item['from']
                        if item['to']:
                            if item['from']:
                                pass
                            else:
                                key=key+'_'+item['to']

                        if key in dict_with_all_valued.keys():
                            if dict_with_all_valued[key]==item['toString']:
                                pass
                            else:
                                dict_with_all_valued[key] = item['toString']
                        else:
                            dict_with_all_valued[key] = item['toString']

            prev_total_label += 1

        #get the list of all the attcahment
        lst = json_data['fields']['attachment']
        #removing the keys which is having None values and adding the multiple attachments if present
        for k,v in dict_with_all_valued.items():
            print k
            if 'Attachment_' in k  and v:
                for i in range(len(lst)):
                    if lst[i]['filename']==v:
                        attachment=attachment+v+'  :   '+lst[i]['content']+'\n'
            elif v:
                dict_updated[k.split('_')[0]]=v
            else:
                pass

        if attachment:
            dict_updated['attachment']=attachment

        return dict_updated,total
    else:
        response.raise_for_status()


def update_cloned_jira(key,dic_with_update,prev_total_label,current_total_label,custom_field_description):
    url = jiraBaseUrl_cisco+'2/issue/'+key
    #Below is the format for updating the JIRA
    update={"update":{}}
    comment=''

    logging.info("INSIDE UPDATED_CLONED_JIRA")
    #Please refer https://developer.atlassian.com/jiradev/jira-apis/jira-rest-apis/jira-rest-api-tutorials/updating-an-issue-via-the-jira-rest-apis
    #to how to update JIRA field
    for k,v in dic_with_update.items():
        if k=="summary":
            update["update"]["summary"]=[]
            update["update"]["summary"].append(dict())
            update["update"]["summary"][0]["set"] = v
        elif k=="description":
            update["update"]["description"] = []
            update["update"]["description"].append(dict())
            update["update"]["description"][0]["set"] = v+custom_field_description
        elif k=="priority":
            if v == 'Very High':
                v = 'Blocker'
            elif v == 'High':
                v = 'Critical'
            elif v == 'Medium':
                v = 'Major'
            elif v == 'Low':
                v = 'Minor'
            else:
                pass

            update["update"]["priority"] = []
            update["update"]["priority"].append(dict())
            update["update"]["priority"][0]["set"] = {}
            update["update"]["priority"][0]["set"]["name"]=v

        else:
            comment=comment+'\n'+"{0}     :     {1}".format(k,v)

    #Add the comment after getting all the comments
    if comment:
        update["update"]["comment"] = []
        update["update"]["comment"].append(dict())
        update["update"]["comment"][0]["add"] = {}
        update["update"]["comment"][0]["add"]["body"]=comment

    #Add the latest total label and remove the old total label from the Cisco Jira
    if prev_total_label<=current_total_label:
        update["update"]["labels"] = []
        if prev_total_label<current_total_label:
            update["update"]["labels"].append(dict())
            update["update"]["labels"][0]["remove"] = "ChangLogIndex_"+str(prev_total_label)
        update["update"]["labels"].append(dict())
        update["update"]["labels"][1]["add"]="ChangLogIndex_"+str(current_total_label)

    return update


