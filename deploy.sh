export IMAGE="europe-west4-docker.pkg.dev/kimo-prod/kimo-images/pdf-parser:latest"
gcloud config set builds/use_kaniko True
gcloud builds submit --tag $IMAGE
