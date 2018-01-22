# systems-jira-sync
Need to create JIRA raise in SKY JIRA for SKY Q HIP 

To authenticate SKY  JIRA server :
 Need to have CEC username and password 
 Need to have certificate.p12 file which we nee to convert into certificate.pem  and keys.pem file using below commands.

 openssl pkcs12 -in satshara.p12 -out keys.pem -nocerts
 
 openssl pkcs12 -in satshara.p12 -nokeys -out certificate.pem

 strip password - backup keys.pem first: 
 openssl rsa -in keys.pem -out keys.pem

 Plz keep this certificate and key file in a seprate file (Certificate folder)

Use same username and password for CISCO JIRA authentication 
 
 
