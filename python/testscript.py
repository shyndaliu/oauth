import pyodbc

server = "oauth.database.windows.net"
database = "oauth_db"
username = "uldanone"
password = "125563_oauth"
driver = "{ODBC Driver 17 for SQL Server}"

with pyodbc.connect(
    "DRIVER="
    + driver
    + ";SERVER=tcp:"
    + server
    + ";PORT=1433;DATABASE="
    + database
    + ";UID="
    + username
    + ";PWD="
    + password
) as conn:
    with conn.cursor() as cursor:
        cursor.execute("create table test(" + "/n" + "test string" + "/n" + " )")
