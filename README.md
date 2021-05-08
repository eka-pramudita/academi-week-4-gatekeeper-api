# Gatekeeper API: Stream Processing of Database User Activity

## Case
In a company, the back end will build a system that can capture all database user activity data. 
As a data engineer we will transport the data in real time and then put it in some 
database (Postgres / BigQuery) so that later the business team will be able to create the 
reports they need. Unfortunately, the backend will not allow us to tap their databases 
since accessing production data directly will potentially harm the database performance. 
The backend team will send the user activity in JSON format so we have to prepare our API (Application Programming Interface) 
called Gatekeeper.

## Tech Stacks

### Flask
Flask is a lightweight WSGI (Web Server Gateway Interface) web application framework. It is designed to make getting 
started quick and easy, with the ability to scale up to complex applications. Flask is used in
this project to create the Publisher API. The Publisher API will validate message, in this project
is the user activity in JSON format, by using a payload. If the message is valid, then it will be
pushed into Pub/Sub cluster. Below is the message payload I use to validate message:
```python
message_payload = {
    "type": "object",
    "properties": {
        "activities": {
            "type": "array",
            "items": {"anyOf": [{"$ref": "#/$defs/insert"}, {"$ref": "#/$defs/delete"}]},
            "minItems": 1
        }
    },
    "$defs": {
        "insert": {
            "type": "object",
            "required": ["operation", "table", "col_names", "col_types", "col_values"],
            "properties": {
                "operation": {"const": "insert"},
                "table": {"type": "string"},
                "col_names": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "col_types": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "col_values": {
                    "type": "array"
                }
            }
        },
        "delete": {
            "type": "object",
            "required": ["operation", "table", "old_value"],
            "properties": {
                "operation": {"const": "delete"},
                "table": {"type": "string"},
                "old_value": {
                    "type": "object",
                    "required": ["col_names", "col_types", "col_values"],
                    "properties": {
                        "col_names": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "col_types": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "col_values": {
                            "type": "array"
                        }
                    }
                }
            }
        }
    }
}
```
### Google Pub/Sub
Pub/Sub is an asynchronous messaging service that decouples services that produce events 
from services that process events. For a more explanation about Pub/Sub, please refer this
[link](https://cloud.google.com/pubsub/docs/overview). 
In this project, Pub/Sub cluster is used to receive and process validated message sent 
by the Publisher API. To have a better understanding on how the messaging transfer goes,
please see the diagram below:
<div align="center">
<img src="https://drive.google.com/uc?export=view&id=1dSwUtLZmzWc4FjJIPlqsa0dDpkA_J-yG">
</div><br />

## Installation
Clone this repository to your preferred directory.
```commandline
git clone https://github.com/eka-pramudita/academi-week4-gatekeeper-api
```

## Requirements
* Python 3.5 or above. Check using this command:
    ```commandline
    python --version
    ```
* Google Cloud SDK. Follow the installation instruction 
  [here](https://cloud.google.com/sdk/docs/install) 
  then add `.\Google\Cloud SDK\google-cloud-sdk\bin` into your environment variable.
  
* Git. Download from [here](https://git-scm.com/downloads) then install. 
  Add `C:\Program Files\Git\bin` into your environment variable.
  
* Service Account Credential. Please refer to this [link](https://cloud.google.com/docs/authentication/getting-started)
to authenticate GCP service using Service Account Credential using json file.
  
## How to Use
1. Open Git Bash terminal.
2. Choose directory using `cd` command to the cloned project directory.
3. I assumed that you already have access to the Google Cloud Platform and set up 
   billing for your project. Configure your Google Cloud by running `gcloud init` command. 
   For step-by-step tutorial please refer this [link](https://www.jhanley.com/google-cloud-understanding-gcloud-configurations/#:~:text=A%20gcloud%20configuration%20is%20a,configuration%20named%20default%20is%20created.&text=The%20creation%20of%20a%20configuration%20can%20be%20accomplished%20with%20gcloud%20or%20manually.).
   
4. Execute `pubsub.sh` to intiate table, topics and subscription creation.
    ```commandline
    bash pubsub.sh
    ```
   
5. Execute `main.py` in `app` folder to run the Publisher API.
    ```commandline
    python -m app.main
    ```
   If your Git Bash terminal looks like this then the API is running successfully.
    <div align="center">
    <img src="https://drive.google.com/uc?export=view&id=1nSepEbZY62-uSQDvtCFhKHIlpVxzmrng">
    </div><br />
   
6. Go to www.postman.com to send your message. Create a workspace, please refer to this 
   [tutorial](https://www.guru99.com/postman-tutorial.html).
   Set the address to `http://localhost/message` and method `POST`. Input the message then send.
   The valid message will be looked like this and will be sent to Pub/Sub cluster:
   <div align="center">
   <img src="https://drive.google.com/uc?export=view&id=15QuasT2W1KACLLxA5oVowSzZ1Hocg_r9">
   </div><br />
   Invalid message will be looked like this and will be counted:
   <div align="center">
   <img src="https://drive.google.com/uc?export=view&id=19oYaoGKut_rImAYv6PnZQ98N9dHFyONR">
   </div><br />
7.  Messages sent to Pub/Sub cluster will be received by Topics and become message queue.
    To consume and process the message queue, execute the `subscriber.py` file in `app` folder.
    ```commandline
    python -m app.subscriber
    ```
    The consumer is running successfully when this is shown in your terminal:
    <div align="center">
   <img src="https://drive.google.com/uc?export=view&id=1yJuEARMsVTArkPOgaVtdrR2vmWMK3T7j">
   </div><br />
    When in listening state, any message you sent will be directly processed in the consumer.

8.  The consumer file processes INSERT and DELETE operation for the table with these cases:
    1. Insert: if the table is not yet available in the db, it will be created accordingly with the fields.
    2. Insert: if the table is already available in the db, but the relevant field does not exists, it will alter table to add relevant field.
    3. Delete: if the table is not available, it will fail the entire transaction and output error.
    
    Please note that INSERT operation always comes before DELETE. 
    Check your bigquery table to confirm the process is successfully done.
    <div align="center">
   <img src="https://drive.google.com/uc?export=view&id=1hhboE9CB93j6uMEWH-TCLGr-Nv5C2dPm">
    <small align="center">Inserted Message</small>
   </div><br />

## Unit Tests
Creating Unit Tests is essential for implementing TDD (Test Driven Development) discipline
in developing web service. In this project, I created 3 unit tests as follows:
1. Test if we're able to navigate to `http://localhost`.
2. Test when entering valid message.
3. Test when entering invalid message.

All test cases are implemented in `/tests/app/test_main.py`. To do the test, run this command line:
```commandline
python -m pytest -s
```
If your Git Bash terminal looks like this then the tests have passed successfully.
<div align="center">
<img src="https://drive.google.com/uc?export=view&id=18dc0xeahmBn5zZyY5r6iEDaPj2ARKeZn">
</div><br />
