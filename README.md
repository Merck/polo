# POLO: web interface to MARCO-scored crystallization images

The [MARCO crystallization classification model](https://doi.org/10.1371/journal.pone.0198883) appears robust for
many sorts of visible crystallization images. This model can be implemented as network service
([see MARCO page on GitHub](https://github.com/tiangolo/tensorflow-models/tree/master/research/marco)) and was also
incorporated into the RockMaker software.

The POLO system is a web interface to access RockMaker images, and is intended to
be a very rapid method to find crystals guided by a classification model such as MARCO.

The motivation behind this effort is two-fold:	
- The RockMaker interface is plate-based. When examining broad screens, a sorted list may be more effective.
- Depending on network configuration, it may become laborious to find crystals from a set of plates in a set of
  experiments, to zoom in on a single image, and to evaluate a time course of images.

## POLO in a nutshell
- Images are scored periodically using an separate image-scoring implementation such as MARCO (this is outside the
  scope of POLO, but a sample script is provided) and stored in a separate database (the "POLO database").
- Quickly navigate or search a project/experiment tree, just as in RockMaker, to select one or more
  plates (useful for broad screens), even if they are from different RockMaker experiments.
- Browse drops, sorted by their MARCO “Crystal” or “Other” scores, or other information such
  as well number, and see the time course. You can filter results by drop number and/or temperature.
- Mark a drop image as "Favorite" (akin to RockMaker’s "Interesting" tag), though this is not saved.
- Export a list to a CSV file for further analysis, for example to include in a report or to bring
  to the lab for sample prep.
- Use keyboard shortcuts (e.g. arrows) for most of the functionality, which makes zipping through images a breeze.
- Manually annotate images using keyboard shortcuts (CPXO, or D for dispute) and is case-insensitive.
  Annotations are stored in the same POLO database which contains the MARCO scores.
- To limit the tree to a single top-level folder (e.g. for one user's experiments), use http://POLOSERVER/?folder=NAME

________________________________________________________________________________

## How to install and run a POLO server

### Databases

- You need a connection to one or more RockMaker databases with read-only permissions (see [Caveats](#caveats)).
    - The connection string will look something like:
      `DSN=NAME_OF_DSN;UID=USERNAME;PWD=PASSWORD;DATABASE=RockMaker`
    - On Windows, you can set up a DSN by going to
      `Control Panel\System and Security\Administrative Tools\ODBC Data Sources`
    - On linux, you need to set up the DSN using unixODBC (and perhaps FreeTDS)
- You need to make RockMaker images available via a URL.
    - An easy way to configure this is to mount the Windows share under linux (let's call it `/mnt/RockMaker`).
    - Then start a server. Using Python2, you can `cd /mnt/RockMaker ; python -mSimpleHTTPServer <PORT>` to
      serve images on port <PORT>. If you use Python 3, try `python -m http.server <PORT>`
- You need a POLO database. Currently this is configured as a MySQL database. See the file called
  `scripts/define_tables.sql` for more information. The RockMaker image server information
  needs to be set up in the `sources` table.
    - The connection string for the POLO database will look something like:
      `USERNAME:PASSWORD@MYSQLHOST:PORT/DATABASE_NAME`
    - This database can be updated regularly (e.g. using a cron entry) by running a suitable script.
      There is a template available called `scripts/Update_POLO.py`.


### Authentication

- To bypass authentication, you can set `BYPASS_AUTH = True` in `polo/config.py`
- To set up OAuth2-based authentication, you'll need to obtain the following bits of information:
    - client_id (looks like a random string)
    - client_secret (also looks like a random string)
    - authorization_base_url (e.g. 'https://OAUTH2_SERVER/authentication-service/v2/authorize')
    - token_url (e.g. 'https://OAUTH2_SERVER/authentication-service/v2/token')
    - userprofile_url (e.g. 'https://OAUTH2_SERVER/authentication-service/v2/userinfo')
    - username_field obtained from the userprofile_url (e.g. 'username')

   
### POLO configuration

- The database connection strings (one for each RockMaker instance, and one for the POLO database)
  should be entered into the file `polo/config.py`. There is a template available called `polo/config.py_TEMPLATE`.
- Permissions on the POLO database should allow for inserting into the `disputes` table and reading all other tables.
- Permissions on the RockMaker database(s) should be read-only (see [Caveats](#caveats)).
- An example `polo/config.py` file looks like:

        class Config(object):
            DEBUG = False
            TESTING = False
            BYPASS_AUTH = False
            DEMO = False

            POLO_CONN = '<POLO CONNECTION STRING>'
            RM_CONN = {
                1: '<ROCKMAKER 1 CONNECTION STRING>',
                2: '<ROCKMAKER 2 CONNECTION STRING>',
                ...
            }
            
            OAUTH2_CLIENT_ID = ...      
            OAUTH2_CLIENT_SECRET = ...      
            OAUTH2_AUTHORIZATION_BASE_URL = ...      
            OAUTH2_TOKEN_URL = ...      
            OAUTH2_USERPROFILE_URL = ...  
            OAUTH2_USERNAME_FIELD = ...
        
        class ProductionConfig(Config):
            pass
        
        class DevelopmentConfig(Config):
            DEBUG = True
            BYPASS_AUTH = True

        class DemoConfig(Config):
            BYPASS_AUTH = True
            DEMO = True

- Be sure that the dictionary of RockMaker instances is reflected in the MySQL `sources` table.
  Again consult the file `scripts/define_tables.sql` for additional information.

### Python configuration (using Anaconda)

If behind a firewall, set the proxy

    export http_proxy=http://proxy_server:port
    export https_proxy=http://proxy_server:port

Create and activate an environment called "polo-env", then install required packages

    conda create -n polo-env python=3.7 -y
    conda activate polo-env 
    conda install sqlalchemy flask flask-cors mysqlclient pyodbc requests-oauthlib -y
    
If this doesn't work, try using `pip install ...` instead.

### Python configuration (using virtualenv)

- Ensure you have a Python 3 installation with the `virtualenv` command
- If behind a firewall, set the proxy as described above
- Create and activate a local virtual environment called "polo-env", then install required packages
- From the same directory which contains `setup.py`:


    virtualenv polo-env
    source ./polo-env/Scripts/activate  # on Windows type .\polo-env\Scripts\activate.bat
    python setup.py install        

### Start the POLO server in development mode

    export FLASK_APP=polo
    export FLASK_ENV=development
    export OAUTHLIB_INSECURE_TRANSPORT=1 # when using authentication with HTTP (not HTTPS)
    flask run -h 0.0.0.0 -p 9002
    
### Caveats<a name="caveats">

- Since the MARCO score in RockMaker is a single weighted combination of scores, it will likely not exactly match
  the individual class scores in POLO.
- POLO has been tested against RockMaker database version 3.15.8.1.
- All RockMaker database connections should be made using read-only accounts to avoid possible
  database corruption and voiding of your maintenance contract.
- Changes to the RockMaker database schema may render POLO useless.
- Formulatrix does not support or recommend use of POLO.
- Please do not approach Formulatrix with POLO-related questions.

### Credits

- Created by Charles A. Lesburg <charles.lesburg@merck.com>
- Thanks to Formulatrix for consenting to the open-source publication of this alternative interface to the RockMaker database

### License

- Distributed under the MIT License. See the LICENSE file for details
- See the LICENSES_THIRD_PARTY file for additional license information
