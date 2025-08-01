import os, psycopg
from psycopg.rows import dictRow

def getConn():
    return psycopg.connect(os.getenv("DATABASE_URL"), rowFactory=dictRow)

def createTables():
    conn = getConn()
    conn.execute("""
        create table if not exists users (
            id serial primary key,
            email text unique,
            password text,
            apiKey text unique
        )
    """)
    conn.commit()
    conn.close()
