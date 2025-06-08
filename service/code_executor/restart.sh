docker ps -a -q | xargs -r docker rm -f && docker images -q | xargs -r docker rmi -f
docker build -t code_executor .
docker run -p 50051:50051 -d code_executor
docker ps