# Copy the files in the docker directory above the polo directory and build the image as so:
# NOTE: any time the source changes, you need to rebuild the image
docker build -t polo .

# run the container as so. Gunicorn (see Dockerfile) serves on port 8080, docker exposes it on 9876. Change as necessary.
docker run -d -it --rm \
       -p 9876:8080 \
       --env-file polo.env \
       --name polo \
       polo
