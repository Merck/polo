# POLO: web interface to MARCO-scored crystallization images

The [MARCO crystallization classification model was published in 2018](https://doi.org/10.1371/journal.pone.0198883)
and seems to be very robust for many sorts of visible crystallization images.
This model has incorporated into the RockMaker software and can be implemented
as an internal network service.

The POLO system is a web interface to access MARCO-classified images, which is intended to
be a very rapid method to find crystals.

The motivation behind this effort is two-fold:	
- The RockMaker interface is plate-based. When examining broad screens, a sorted
  list may be more effective.
- Depending on network configuration, the RockMaker interface can be slow and it may become
  laborious to find crystals on a set of plates in a set of experiments, to zoom in on a
  single image, and to evaluate a time course of images.

## POLO in a nutshell
- Images are scored periodically using an separate MARCO implementation (this is outside the
  scope of POLO). Note that the RockMaker MARCO scores are a weighted combination of scores,
  so will not match exactly the scores in POLO. These scores are stored in a MySQL database.
- Quickly navigate or search a project/experiment tree, just as in RockMaker, to select one or more
  plates (useful for broad screens), even if they are from different RockMaker experiments.
- Browse drops, sorted by their MARCO “Crystal” or “Other” scores, or other information such
  as well number, and see the time course. You can filter results by drop number and/or temperature.
- “Favorite” a drop (akin to RockMaker’s “Interesting” tag), though this is not saved.
- Export a list to a CSV file for further analysis, for example to include in a report or to bring
  to the lab for sample prep.
- Keyboard shortcuts (e.g. arrows) for most of the functionality, which makes zipping through
  images a breeze.
- You can manually annotate images using keyboard shortcuts
  (CPXO, D for dispute, and S for salt/false positive). Annotations
  are stored in the same MySQL database which contains the MARCO scores.
- You can limit the tree to a single top-level folder, use http://POLOSERVER/?folder=NAME

________________________________________________________________________________

## How to run a POLO server from a Docker container

Download the POLO code from [github.com](https://github.com/merck/polo).

    mkdir polo-docker
    cd polo-docker
    git clone ...


Build the POLO Docker container. Put the following into a file called `Dockerfile` in the current directory.

    FROM python:3.7-slim

    # if you are behind a firewall, you may need to set the https proxy to enable downloading of external content
    ENV https_proxy "http://webproxy.company.com:8080"

    RUN apt-get update && apt-get -y install \
            build-essential \
            unixodbc \
            unixodbc-dev \
            tdsodbc \
            freetds-bin \
            freetds-dev \
            mariadb-client \
            mariadb-common \
            libmariadbclient-dev \
            host
    WORKDIR /app
    COPY polo/requirements.txt .
    RUN pip3 install -r requirements.txt
    COPY polo .
    CMD bash freetds.sh && gunicorn --bind=0.0.0.0:9002 --workers=5 --preload polo:app


Build the POLO image (let's call it "polo")

    docker build -t polo .


All settings are configured using a file called `polo.env` where each line is a key=value pair
An example `polo.env` file looks like this:

    FLASK_ENV=production

    #POLO_INFO=an informational message
    #POLO_WARNING=a warning message
    #POLO_ERROR=an error message

    # POLO database connection information
    POLO_CONN=user:password@server/database

    # RockMaker server configuration. The index should match the id in the POLO database `sources` table
    # Up to 10 RockMaker databases can be specified
    # Specify EITHER RM_x_PORT or RM_x_INSTANCE
    RM_1_HOST=
    RM_1_PORT=
    RM_1_UID=
    RM_1_PWD=
    RM_1_DATABASE=

    RM_2_HOST=
    RM_2_INSTANCE=
    RM_2_UID=
    RM_2_PWD=
    RM_2_DATABASE=

    # OAuth2 configuration, or set BYPASS_AUTH to True
    BYPASS_AUTH=False
    OAUTH2_AUTHORIZATION_BASE_URL=
    OAUTH2_TOKEN_URL=
    OAUTH2_USERPROFILE_URL=
    OAUTH2_USERNAME_FIELD=
    OAUTH2_CLIENT_ID=
    OAUTH2_CLIENT_SECRET=

    # If running the POLO Docker container behind a reverse proxy server (e.g. nginx) or running over HTTP
    OAUTHLIB_INSECURE_TRANSPORT=1


You should have a directory structure which looks like this:

    Dockerfile (file)
    polo.env (file)
    polo (directory)

Configure the `polo.env` file and run the container in the background, in this case over port 9002.

    docker run -d -it --rm -p 9002:9002 --env-file polo.env --name polo polo


### The POLO Database

- You need a POLO database. Currently this is configured as a MySQL database. See the file called
  `scripts/define_tables.sql` for more information. The RockMaker image server information
  needs to be set up in the `sources` table.
    - The connection string for the POLO database will look something like:
      `USERNAME:PASSWORD@MYSQLHOST:PORT/DATABASE_NAME`
    - This database can be updated regularly (e.g. using a cron entry) by running a suitable script.
      There is a template available called `scripts/Update_POLO.py`.


### Image server(s)

- You need to serve RockMaker images
    - An easy way to configure this is to mount the Windows share under linux (let's call it `/mnt/RockMaker`).
    - Then start a server. Using Python2, you can `cd /mnt/RockMaker ; python -mSimpleHTTPServer <PORT>` to
      serve images on port <PORT>.
    - If you use Python 3, try `python -m http.server <PORT>`

- Be sure that the dictionary of RockMaker instances is reflected in the MySQL `sources` table.
  Again consult the file `scripts/define_tables.sql` for additional information.

    
### Credits

- Created by Charles A. Lesburg <charles.lesburg@merck.com>


### License

- Distributed under the MIT License. See the LICENSE file for details
- See the LICENSES_THIRD_PARTY file for additional license information
