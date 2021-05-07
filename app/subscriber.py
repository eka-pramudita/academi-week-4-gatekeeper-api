import time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
import os
import json
from google.cloud import bigquery

project_id = "academi-cloud-etl"
subscription_id = "subscription-semalam"
# Number of seconds the subscriber should listen for messages
timeout = 60.0
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

subscriber = pubsub_v1.SubscriberClient()
# The `subscription_path` method creates a fully qualified identifier
# in the form `projects/{project_id}/subscriptions/{subscription_id}`
subscription_path = subscriber.subscription_path(project_id, subscription_id)

messages = []

def callback(message):
    print(f"Received {message.data}.")
    message.ack()
    str_data = str(message.data).replace("\\", "").replace("rn", "").replace("b\'b\'", "").replace("\'\'", "").replace(" ", "")
    json_data = json.loads(str_data)
    insert = [obj for obj in json_data["activities"] if obj["operation"] == "insert"]
    delete = [obj for obj in json_data["activities"] if obj["operation"] == "delete"]

    # BigQuery section
    client = bigquery.Client()
    table_id = project_id + ".gatekeeper_api." + insert[0]["table"]
    ## Insert
    for j in range(len(insert)):
        ins = {}
        for i in range(len(insert[j]["col_names"])):
            ins[insert[j]["col_names"][i]] = insert[j]["col_values"][i]
        rows_to_insert = [ins]

        # TODO still failed when the table does not exist. Fix the issue
        try:
            client.insert_rows_json(table_id, rows_to_insert)
        except:
            schema = []
            for i in range(len(insert[j]["col_names"])):
                field = bigquery.SchemaField(insert[j]["col_names"][i], insert[j]["col_types"][i])
                schema.append(field)

            table = bigquery.Table(table_id, schema=schema)
            client.create_table(table)
        client.insert_rows_json(table_id, rows_to_insert)

    ## Delete
    # TODO still unable to delete rows. Fix query (?)
    for j in range(len(delete)):
        condition = ' AND '.join([str(delete[j]["old_value"]["col_names"][i])+"="+str(delete[j]["old_value"]["col_values"][i])
                                  for i in range(len(delete[j]["old_value"]["col_names"]))])
        table_id = project_id + ".gatekeeper_api." + delete[j]["table"]
        delete_query = f""" DELETE FROM `{table_id}` WHERE {condition}"""
        try:
            client.get_table(table_id)
            
            client.query(delete_query)
        except:
            print("Table does not exist, transaction is cancelled")


streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")

# Wrap subscriber in a 'with' block to automatically call close() when done.
with subscriber:
    try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()


