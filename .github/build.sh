exit
TOKEN=$1
echo $TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker build . -t trisagent
docker build composition/dashboard -t ghcr.io/orchestrading/dashboard:latest
docker build composition/epa_bot -t ghcr.io/orchestrading/epabot:latest
docker build composition/log_manager -t ghcr.io/orchestrading/logmanager:latest
docker build composition/ibkr_middleware -t ghcr.io/orchestrading/ibkrmiddleware:latest
docker push ghcr.io/orchestrading/dashboard:latest
docker push ghcr.io/orchestrading/epabot:latest
docker push ghcr.io/orchestrading/logmanager:latest
docker push ghcr.io/orchestrading/ibkrmiddleware:latest

