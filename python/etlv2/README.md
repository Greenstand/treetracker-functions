Run the following command to create a virtual environment (replace myenv with your preferred name):
`python3 -m venv myenv`

## Activate the virtual environment:

#### On Windows: `myenv\Scripts\activate`

#### On macOS/Linux: `source myenv/bin/activate`

## Install requirements

`pip install -r requirements.txt`

## Set up Database Access Credential in .env

Create an .env file in the project directory to configure your database login credentials.

`touch .env`

Edit the .env file and copy the following key-value configs, update the values according to your actual database access credential.

```
SRC_DB_HOST=localhost
SRC_DB_PORT=5432
SRC_DB_NAME=mydatabase
SRC_DB_USER=myuser
SRC_DB_PASSWORD=mypassword

DEST_DB_HOST=localhost
DEST_DB_PORT=5432
DEST_DB_NAME=mydatabase
DEST_DB_USER=myuser
DEST_DB_PASSWORD=mypassword
```

## Activate Environment Variables:

Activate the environment variables by sourcing the .env file in your terminal: `source .env`

## Run Application:

Run the application using: `python migration_job.py`
