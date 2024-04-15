Run the following command to create a virtual environment (replace myenv with your preferred name):
`python3 -m venv myenv`

## Activate the virtual environment:

#### On Windows: `myenv\Scripts\activate`

#### On macOS/Linux: `source myenv/bin/activate`

## Install requirements

`pip install -r requirements.txt`

## Create an Environment Variable File

Create a .env file in the project directory to store environment variables.
Open the .env file and add the following key-value configs, update the values.

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

## Update config.properties file

### Parsing the config file makes use of configparser, so the square brackets such as [job] represents sections and should not be deleted. In case you are commenting a part of a key/value pair, makes ure to leave a space before. e,g: key=1,23 #456

```
#section name job - job configs
[job]
# here job is scheduled to run every 24 hours, set value to preferred frequency
job_interval_seconds=86400
# number of iterations to run (0) means to run continuously, unless manually stopped
max_iterations=0
# set batch size for each run, 1000 here means a limit of 1000 records per batch of query
query_batch_size=1000
# list of organization_ids separated by commas
organization_ids=15,1,13,14,2,3,4,5,6,30,31,32,11

#section name queries
[queries]
list of queries being run for data migration
#[columns] will be replaced by list of columns specified in columns section below
organization_query = select [columns] from table

#section name columns: columns to migrate
[columns]
list of columns to migrate for each query
```

## Activate Environment Variables:

Activate the environment variables by sourcing the .env file in your terminal: `source .env`

## Run Application:

Run the application using: `python migration_job.py`
