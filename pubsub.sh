# src/pubsub.sh

export GOOGLE_APPLICATION_CREDENTIALS="key.json"

bq --location=US mk --dataset academi-cloud-etl:gatekeeper_api

gcloud pubsub topics create topic-semalam
gcloud pubsub subscriptions create subscription-semalam --topic=topic-semalam