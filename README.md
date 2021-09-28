# SolTech-Automation-Manager-io

## ENV variables Set up in heroku

```bash
- MANAGER_USERNAME
- PASSWORD
- API_KEY
- EMAIL_ADDRESS
- APP_KEY
- COMPANY_NAME
```

The MANAGER_USERNAME represents the username for the manager.io account.
The PASSWORD represents the password for the manager.io account.

The API_KEY is the KEY that is returned in the json example:

https://{yourcompanyurl}/api
example: https://solltech.manager.io/api

Example Result:
```json
[
    {
        "Key": "c29sbHRlY2g",
        "Name": "solltech"
    }
]  
```
In this case the API_KEY would be: "Key": "c29sbHRlY2g",
API_KEY = c29sbHRlY2g

The EMAIL_ADDRESS represents the address that will do all the emailing.

The APP_KEY otherwise known as the app password is what is used to keep the emailing account safe.
    To retrive the APP_KEY for the email account see the following guide:
    [Gmail App password setup](https://support.google.com/mail/answer/185833?hl=en-GB)

The COMPANY_NAME is the fill name of the URL example:
    your manager.io url: https://solltech.manager.io/api
        COMPANY_NAME = solltech.manager.io
    

## Usage
After setting up the ENV Variables in heroku simply run the application.

## NOTE!
After the application has ran all payslips that have been emailed will be deleted.

In the case a payslip has not been emailed means that the payslips is missing important data such as Contributions.

The local .env file contains credentials for a test account and a test emailing account. And not to worry the file is within the .gitignore so it will not be pushed


Test account:
```bash
- MANAGER_USERNAME=administrator
- PASSWORD=6a4a6a4f98
- API_KEY=c29sbHRlY2g
- EMAIL_ADDRESS=hakeem.watson691@gmail.com
- APP_KEY=jiguhcxkauvcoxin
```
