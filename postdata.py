import json
import os
from authentication_Sky import *
from issues import *
import logging

logger = logging.getLogger('MAIN ')
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def main():
    except_flag=False
    is_jira=True
    url=jiraBaseUrl_cisco + '2/issue'
    prev_total_label=None
    default_total_label=None

    logger.info("JIRA sync-up ...")
    #authenticate the CISCO JIRA server
    session=authenticate()


    try:
        #search all the issue objects
        issues,total = search_project_issues(FirstJira)
        dict_of_customfield=custom_field()
    except Exception,e:
        logger.error("Excetption occured while searching for issues or in getting the customfield" + str(e))
        sys.exit(1)

    while (is_jira and total>0):
        for issue in  issues:
            if issue.components()=="Fusion Development" and str(issue.fixVersions()).find("Sky Q HIP") == 0:
                try:
                    label_url=jiraBaseUrl_cisco+"2/search?jql=project='SKY Q Hybrid IP E2E' AND labels in ("+ str(issue.key())+") AND labels in (SKY_JIRA)"
                    response=session.get(label_url)

                    if response.status_code==200:
                        label_json_data=response.json()
                        if len(label_json_data['issues'])!=0:
                            logger.info("Cloned Jira :  "+label_json_data['issues'][0]['key']+" (Sky Jira : "+ str(issue.key())+")")

                            #Now get the custom field description
                            gen_description = issue.gen_desc(dict_of_customfield)
                            #This will be default TOTAL value in case if ChangLogIndex_ is not present in the label
                            default_total_label=sky_hist_total(issue.key())

                            #Now find the label with "ChangLogIndex_" in CISCO JIRA issue which is containing the last TOTAL count(X) of history for SKY JIRA
                            csc_url_label=jiraBaseUrl_cisco+"2/issue/"+str(label_json_data['issues'][0]['key'])
                            resp_label=session.get(csc_url_label)

                            if resp_label.status_code==200:
                                issue_label_json_data=resp_label.json()
                                label_list = issue_label_json_data["fields"]["labels"]
                                for label in label_list:
                                    if "ChangLogIndex_" in label:
                                        prev_total_label=label.split('_')[1]
                                        break
                                if not prev_total_label:
                                    prev_total_label=default_total_label
                            else:
                                resp_label.raise_for_status()

                            # get the update from the SKY-JIRA according to history on the basis of prev_total_label(check history after prev_total_label(X) value)
                            hist_update_dict, current_total_label = history(issue.key(), int(prev_total_label))

                            #Check  hist_update_dict is not empty
                            if bool(hist_update_dict) or prev_total_label==default_total_label:
                                # Create the json data from hist_update_dict
                                # so as to update the CISCO JIRA and add the customfield description also
                                updated_data_dictionary=update_cloned_jira(issue.key(),hist_update_dict,int(prev_total_label),int(current_total_label),gen_description)
                                update_url=jiraBaseUrl_cisco+'2/issue/'+str(label_json_data['issues'][0]['key'])
                                res = session.get(update_url)
                                if res.status_code==200:
                                    update_res = session.put(update_url, json=updated_data_dictionary)
                                    if update_res.status_code==204:
                                        logging.info("Added the update data to CISCO JIRA issue number  :"+str(label_json_data['issues'][0]['key']))
                                    else:
                                        update_res.raise_for_status()
                                else:
                                    res.raise_for_status()
                            else:
                                logging.info("No update in the updated_data_dictionary  for issue number  :" +str(label_json_data['issues'][0]['key']))

                            continue
                    else:
                        response.raise_for_status()

                    gen_description=issue.gen_desc(dict_of_customfield)
                    attachments = getAttachment(issue.key())
                except Exception, e:
                    logger.error("Catching the exception here" + str(e))
                    except_flag=True
                    break

                data = {
                        "fields": {
                        "summary": "["+ str(issue.key())+"] "+str(issue.title()),
                        "issuetype": {
                        "name": str(issue.type()),
                        "subtask": "false"},
                        "description": str(issue.description())+attachments+gen_description,
                        "priority": {
                        "name": str(issue.priority())},
                        "labels": ["SKY_JIRA",issue.key()],
                        "project": {
                               "key": "SQHIP",
                               "name": "Sky Q Hybrid IP E2E"
                                    }
                            }
                        }

                try:
                    logger.info("Add issue: "+ issue.key())
                    response = session.post(url, json=data)
                    if response.status_code==201:
                        logger.info("Created Jira is " + str(issue.key()))
                    else:
                       logger.info("Response is " + str(response.status_code))
                       response.raise_for_status()

                except Exception, e:
                    except_flag=True
                    logger.error("Exception :"+ str(e))
                    logger.error("posting failed for JIRA number : "+ issue.key())
                    break
            else:
                pass


        if except_flag :
            is_jira=False
        else:
            try:
                issues, total = search_project_issues(issue.key())
            except Exception, e:
                logger.info("Last Created Jira was " +str(issue.key()))
                logger.error(" failed for retrieved JIRA so writing the last JIRA number in the file " +str(e) )
                is_jira=False

    logger.info("Latest Jira Id :" +str(issue.key()))


if __name__ == '__main__':
  main()
