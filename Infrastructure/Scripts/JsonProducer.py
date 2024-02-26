import psycopg
import json
import requests


def get_data():
    """ query data from the postgres subscription table to create the table of subscriptions"""
    conn = None
    data = {}

    try:
        # Connection to the database
        conn = psycopg.connect("host=localhost port=5050 dbname=blueCity user=admin password=admin" )
        cur = conn.cursor()

        # Retreive the list of all topics in the dataBase 
        cur.execute("SELECT DISTINCT topic_id FROM subscriptions")
        row = cur.fetchone()
        topic_list= []
        while row is not None:
            topic_list.append(row[0])
            row = cur.fetchone()
        
        # Create the lists of subscriptions for each topics and roles
        role_list = ["admin","consumer","producer"]
        for topic in topic_list:
            for role in role_list:
                topic_sub =[]
                key= topic+"_"+role
                cur.execute("SELECT user_id FROM subscriptions WHERE topic_id = %s AND role = %s",(topic, role))
                row = cur.fetchall()
                if row : 
                    for sub in row:
                        topic_sub.append(sub[0])
                data[key]=topic_sub
        cur.close()
 
    except (Exception, psycopg.DatabaseError) as error:
        print("Error while getting the subscription data:")
        print(error)

    finally:
        if conn is not None:
            conn.close()
        return data

def formatJson(data):
    """ Use the table of subscriptions to format it in Json and wite it in a file"""
    fileData={}
    fileData["topics"]=data

    try:
        with open("data.json", "w") as outfile:
            json_object = json.dumps(fileData, indent=4)
            outfile.write(json_object)

    except Exception as error:
        print("Error while writing the file:")
        print(error)
    finally:
        return fileData


def publishToOpa(data):
    try:
        url = "http://localhost:8181/v1/data"
        response = requests.put(url, json=data)
        return(response)
    except Exception as error:
        print("Error while sending data to OPA")
        print("MAKE SURE THAT YOU LAUNCHE THE KUBECTL PORT FORWARDING FOR OPA WITH: kubectl port-forward svc/opa 8181:8181 ")
        print("Error message: ")
        print(error)

    

if __name__ == '__main__':
   data = formatJson(get_data())
   print("------------------------")
   print("------------------------")
   print("DATA COLLECTED:")
   print(json.dumps(data, indent=4))
   print("------------------------")
   print("------------------------")
   print("Sending Data to OPA")
   resp = publishToOpa(data)
   print("Response from server:")
   print(resp)

