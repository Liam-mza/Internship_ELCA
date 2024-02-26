# The Blue City Platform PoC

This is the first version of the PoC for the real time data streaming platform for the Blue City Project during my internship at ELCA


# Folders
Here is a quick description of the two folders.
## Infrastructure 

This folder contains all the files needed to deploy the kubernetes infrastructure of the platform. 
This means :

 - The Kafka cluster
 - The Postgres DB
 - The OPA server 
 - The Keycloak server 
 - An instance of a Kafka Gateway
 
 It also contains some scripts and some helpers files to interact with Keycloak, OPA and Postgres directly.
 **You will also find the *Startup* script which deploy the whole infrastructure.**

## Web App

This folder contains all the files needed to launch the Web App.

# Requirements

To run the platform you will need to install on you computer the following:

 - Docker
 - Minikube
 - Python (Make sure to have pip to install all required libraries)
 
 
To test your installation of Docker and minikube run the following commands :

     minikube start --memory=4096 --cpus=4

     kubectl get pod -A --watch

# How to launch the platform

Make sure to have all the requirements above installed before following these steps.

Please not that all these steps are meant to be performed on Windows in the command prompt.

## The infrastructure

Start by deploying the infrastructure on kubernetes :

 1. start the docker engine
 2. start minikube with the command:  `minikube start --memory=4096 --cpus=4`
 3. Launch the startup script with : `startup.bat`
 4. Wait for the script to run completely (It should finish with the opening of 3 cmd windows running port forwarding commands)
 5. Do not close the windows opened by the script while you want to use the platform.
 
**Note**: The script will open a window where you are able to follow the deployment of the different pods. Pay attention to this window to check that all pods are correctly starting and does not enter in an error state. Please read the troubleshooting section for debugging tips.

## The Web App

Once the infrastructure is properly deployed you can start the Web App:

 1. Connect to the Keycloak realm on you browser at:  http://localhost:8080/
 2. Login to the admin console with credentials: *admin/admin*
 3. On the top left change the realm from Master to **Demo**.
 4. On the Clients tab click on *import client*.
 5.  Then click on *browse* and import the file *app_Client_config* from the Web App folder.
 6. Click on save at the bottom of the page.
 7. On the Web App folder run the *app.py* file to start the web app.
 8. You can access the web app on you browser at: http://127.0.0.1:5000
 
 Please refer to the readme from the Web App folder for more precision on the functionalities.

# How to kill the infrastructure
Once done you just need to run the command `minikube delete` to delete all kubernetes resources and shutdown minikube.

You can now shutdown the docker engine.

# How to interact with the Kafka cluster

While all creation and management interactions about topics and subscription are done through the web app when it comes to Producing and Consuming Data to/from the Kafka it has to be done via the Kafka Gateway.

The gateway is already deployed by the *startup* script and is ready to be used:

 1. On a new cmd window run the command: `kubectl exec -ti kafka-client-shell /bin/bash`
 2. You have now access to the shell of the Kafka gateway pod
 3. Go to the bin repository with : cd bin/
 4. Import the connection configuration with the following command:
	 

	    cat > /tmp/cff.properties << EOF
	    security.protocol=SASL_PLAINTEXT
	    sasl.mechanism=OAUTHBEARER
	    sasl.jaas.config=org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required \
	      oauth.client.id="CFF-Gateway" \
	      oauth.client.secret="CFF-Gateway-secret" \
	      oauth.token.endpoint.uri="http://keycloak:8080/auth/realms/demo/protocol/openid-connect/token" ;
	    sasl.login.callback.handler.class=io.strimzi.kafka.oauth.client.JaasClientOauthLoginCallbackHandler
	    EOF

**Note**: change the value of  *oauth.client.id* and *oauth.client.secret* to match the credentials of an existing clients. You can use the *Gateway-client-import* file from the infrastructure folder to import new clients to your realm. 

5. Now you are ready to consume or produce data:
	- 5.1. To consume: `./kafka-console-consumer.sh --bootstrap-server my-cluster-kafka-bootstrap:9092 --topic Train --from-beginning --consumer.config=/tmp/cff.properties`
	- 5.2. To produce: `./kafka-console-producer.sh --bootstrap-server my-cluster-kafka-bootstrap:9092 --topic Train --producer.config=/tmp/cff.properties`
	
    **Note**: for each command pay you can change the value "*Train*" to match the topic you want to access and change the config file to match the credentials you to use for authentication.

# Debugging & Troubleshooting

Here are some general tips for debugging and some known problems troubleshooting.

## Accessing the log of kubernetes pod

If you have a pod entering an error state you access its log with the command : 

    kubectl logs *PODNAME*


## Getting info on OPA decision

Opa is deployed with the logging mode activated. 

This means that for each query it will log the input it received and the decision made from this input. 

This can be useful when new policies are not behaving as expected. 

To access this log you just need to access the log of the OPA pod with the command:

    kubectl logs *PODNAME*

##  Interacting directly with OPA 
Sometimes it can be useful to directly query OPA from the command line to check its decisions or the data it has internally. 

You can query it from your localhost via the cmd prompt thanks to the port forwarding. 

Here are some example commands: 

 - Allow to make an authorization query with the given input:


	`curl --request POST --url http://opa.default.svc:8181/v1/data --header 'Content-Type: application/json' --data '{"input": {"topic":"Water","action": "Read","type": "Topic","user": "Ville"}}'`

 - Allow to push external data to OPA that it will use on top of the input to make a decision:


    `curl --location --request PUT 'http://opa.default.svc:8181/v1/data' --header 'Content-Type: text/plain' --data '{"topics": {"Water_admin": ["Ville"],"Water_producer": [],"Water_consumer": ["Post","Police"],"Elec_admin":["Ville"],"Elec_producer": ["Post"],"Elec_consumer": ["Police"]}}'`

- Allow to get the external data used by OPA on top of the input to make a decision:  
	
	`curl --request GET --url http://localhost:8181/v1/data`

##  Zookeeper is running but the Kafka pods are not deployed
This is an issue that may happen during the execution of the startup script.

Everything will be working fine except that when the zookeeper pod is ready the Kafka pods will never be deployed and the script will just wait infinitely.

If you check the logs of the zookeeper pods you will see a very long error stack with a `Java.net.SocketException: Unresolved address` error.

This is due to an internal DNS error from zookeeper and Kafka blocking the deployment. 

To solve this you just need to destroy the infrastructure with `minikube delete` and then restart the docker engine. 
Once done you can deploy the infrastructure normally and everything should be fine. In some rare cases the problem persist and you  need to on top of previous steps to restart you computer.