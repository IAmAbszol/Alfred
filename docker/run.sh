#/bin/sh

docker run --tty --interactive --network=host --env DISPLAY=$DISPLAY --volume $XAUTH:/root/.Xauthority alfred/dev:latest bash
