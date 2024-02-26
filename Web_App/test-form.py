import requests as rq
import json


def checkIfAdmin(user,topic):
    jsonTemplate= {"input":{"name": user,"topic": topic}}

    try:
        url = "http://localhost:8181/v1/data/app/authz/is_admin"
        response = rq.post(url, data=json.dumps(jsonTemplate, indent=2))
        result = response.json().get("result")
        if result == None:
            return False
        return(result)
    
    except Exception as error:
        print("Error while sending data to OPA")
        print("MAKE SURE THAT YOU LAUNCHED THE KUBECTL PORT FORWARDING FOR OPA WITH: kubectl port-forward svc/opa 8181:8181 ")
        print("Error message: ")
        print(error)
        return False





if __name__ == '__main__': 
    print((checkIfAdmin("Ville","Water")))