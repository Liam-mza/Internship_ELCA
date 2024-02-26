import psycopg
import json
import requests


def populate_data():
    """ Create and populate the table of subscriptions"""
    conn = None
    try:
        # Connection to the database
        conn = psycopg.connect("host=localhost port=5050 dbname=blueCity user=admin password=admin" )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS subscriptions;")
        cur.execute("""
            CREATE TABLE subscriptions (
                user_id VARCHAR,
                topic_id VARCHAR,
                role VARCHAR,
                PRIMARY KEY(user_id, topic_id)
            );""")
        
        cur.execute("DROP TABLE IF EXISTS topics;")
        cur.execute("""
            CREATE TABLE topics (
                topic_id VARCHAR,
                owner VARCHAR,
                description VARCHAR,
                PRIMARY KEY(topic_id)
            );""")
        
        with open("db_insert_sub.txt", "r") as outfile:
            # Retreive all lines of the Txt file and insert it in the DB
            lines = outfile.readlines()
            for l in lines:
                values = l.strip().split(",")
                cur.execute("INSERT INTO subscriptions (user_id, topic_id, Role) VALUES (%s,%s,%s);",(values[0],values[1],values[2]))

        with open("db_insert_top.txt", "r") as outfile:
            # Retreive all lines of the Txt file and insert it in the DB
            lines = outfile.readlines()
            for l in lines:
                values = l.strip().split(",")
                cur.execute("INSERT INTO topics (topic_id, owner, description) VALUES (%s,%s,%s);",(values[0],values[1],values[2]))

        print("State of the sub DB after insert:")
        cur.execute("SELECT * FROM subscriptions")
        for record in cur:
            print(record)

        print("State of the topic DB after insert:")
        cur.execute("SELECT * FROM topics")
        for record in cur:
            print(record)

        cur.close()
 
    except (Exception, psycopg.DatabaseError) as error:
        print("Error while creating the subscription table:")
        print(error)

    finally:
        if conn is not None:
            conn.close()


