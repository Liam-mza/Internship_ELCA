# The Blue City Platform PoC - Infrastructure  

This is the first version of the PoC for the real time data streaming platform for the Blue City Project

Here is a quick descrption if the files within this forlder


# Kafka

This folder only contains the YAML file that strimzi will use to deploy the kafka cluster.

This file is configured to have Kafka using keycloak for authentication and OPA for authorization.

# Keycloak
This folder contains the config files to deploy the keycloak server :

**keycloak_imported.yaml**: 
This file deploy a Keycloak server with the demo realm (as defined in the *demo-realm.json* file) already imported to be ready to be used with kafka. This is the file used by the *startup* script.


**keycloak-configmap.yaml**:
This file contains the info of the demo realm (the same content as *demo-realm.json*) and is the one used during the deployement of the Keycloak server to automatically import the demo realm.


**keycloak.yaml**:
This is a plain version of the Keycloak server meaning that no realm is imported at deployment time.

# OPA

This folder contains the config files to deploy the OPA server as well as the file containing the policies used by OPA.

**OPA.yaml** :
This is the config file used to deploy the OPA server. 

The server will be loaded with the policies for the following files:

**app_policies.rego**: 
Defines the policies used to answer to queries coming from the web app.

**good_policies.rego**:
Defines the policies used to answer to queries coming from the kafka.

# DB

This folder contains all the files used to deploy the postgres database.

To better understand the utility of each file you can refer to this well written article: https://www.airplane.dev/blog/deploy-postgres-on-kubernetes

# Scripts

These are some helper script to push data to the DB or Push Data from the Db to OPA.

They are here just for test purposes and not used in the platform.