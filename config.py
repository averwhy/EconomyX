import os, json

SECRETS = json.load(open(os.environ['SECRETS']))

dbuser = SECRETS['pg_user']
dbpassword = SECRETS['pg_pw']
dbname = SECRETS['pg_db']

def db_dsn():
    return f"postgres://{dbuser}:{dbpassword}@pg-server:5432/{dbname}" # Replace pg-server with the docker container name for the postgres server

token: str = SECRETS['token']

webhook: str = SECRETS['webhook']