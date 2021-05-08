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

def callback(message):
    print(f"Received {message.data}.")
    message.ack()
    # Normalize message
    str_data = str(message.data).replace("\\", "").replace("rn", "").replace("b\'b\'", "").replace("\'\'", "").replace(" ", "")
    json_data = json.loads(str_data)
    insert = [obj for obj in json_data["activities"] if obj["operation"] == "insert"]
    delete = [obj for obj in json_data["activities"] if obj["operation"] == "delete"]

    # BigQuery section
    client = bigquery.Client()
    ## Insert
    for j in range(len(insert)):
        tables = client.list_tables(project_id + ".gatekeeper_api")
        bq_table_name = [table.table_id for table in tables]
        table_id = project_id + ".gatekeeper_api." + insert[j]["table"]
        ins = {}
        for i in range(len(insert[j]["col_names"])):
            ins[insert[j]["col_names"][i]] = insert[j]["col_values"][i]
        rows_to_insert = [ins] # Rows to be inserted
        if insert[j]['table'] in bq_table_name:
            if client.insert_rows_json(table_id, rows_to_insert)[0]['errors'][0]['message'] == 'no such field.':
                # Handle non-existent column
                table = client.get_table(table_id)  # Make an API request.
                new_column = client.insert_rows_json(table_id, rows_to_insert)[0]['errors'][0]['location']
                col_names = insert[j]["col_names"]
                col_types = insert[j]["col_types"]
                original_schema = table.schema
                new_schema = original_schema[:]  # Creates a copy of the schema.
                new_schema.append(bigquery.SchemaField(new_column, col_types[col_names.index(new_column)]))

                table.schema = new_schema
                table = client.update_table(table, ["schema"])

                if len(table.schema) == len(original_schema) + 1 == len(new_schema):
                    print("A new column has been added.")
                else:
                    print("The column has not been added.")
            else:
                client.insert_rows_json(table_id, rows_to_insert)
        else:
            # Handle non-existent table by creating a new one
            schema = []
            for i in range(len(insert[j]["col_names"])):
                field = bigquery.SchemaField(insert[j]["col_names"][i], insert[j]["col_types"][i])
                schema.append(field)
            table = bigquery.Table(table_id, schema=schema)
            table = client.create_table(table)
            print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
            errors = client.insert_rows_json(f"{table.project}.{table.dataset_id}.{table.table_id}", rows_to_insert)
            if errors == []:
                print("New rows have been added.")
            else:
                print("Encountered errors while inserting rows: {}".format(errors))
    ## Delete
    for j in range(len(delete)):
        tables = client.list_tables(project_id + ".gatekeeper_api")
        bq_table_name = [table.table_id for table in tables]
        table_id = project_id + ".gatekeeper_api." + delete[j]["table"]
        # Setting up condition query
        cond = []
        for i in range(len(delete[j]["old_value"]["col_names"])):
            if str(delete[j]["old_value"]["col_types"][i]) == "STRING":
                where = str(delete[j]["old_value"]["col_names"][i]) + " = '" + str(delete[j]["old_value"]["col_values"][i]) + "'"
                cond.append(where)
            else:
                where = str(delete[j]["old_value"]["col_names"][i]) + " = " + str(delete[j]["old_value"]["col_values"][i])
                cond.append(where)
        condition = ' AND '.join(cond)
        delete_query = f""" DELETE FROM `{table_id}` WHERE {condition}"""
        if delete[j]['table'] in bq_table_name:
            query_job = client.query(delete_query) # Make an API request.
            query_job.result()
            print(f"Deletion on {delete[j]['table']} success.")
        else:
            print(f"Table does not exist, transaction {j} is cancelled")


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


