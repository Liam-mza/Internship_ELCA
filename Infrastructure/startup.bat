Rem Launch the keycloak instance
kubectl apply -f Keycloak/keycloak-configmap.yaml

timeout 5

kubectl apply -f Keycloak/keycloak_imported.yaml

echo THE SCRIPT WILL WAIT FOR THE KEYCLOAK POD TO BE READY, THIS MAY TAKE A WHILE, YOU CAN CHECK THE STATUS OF THE PODS IN THE CMD WINDOWS THAT THE SCRIPT OPENED.
echo IF THE POD HAS AN ERROR STATE KILL THE SCRIPT TO NOT WAIT 2H FOR TIMEOUT.
start cmd.exe /k kubectl get pod --watch
kubectl wait --for=condition=Ready pods --all --timeout=8040s


Rem Launch the OPA instance and its config map which contain the rules defined in the given rego file
cd OPA
kubectl create configmap example-policy --from-file=Policies/good_policies.rego --from-file=Policies/app_policies.rego
kubectl apply -f OPA.yaml
cd..

Rem Launch the Postgress DB instance
kubectl apply -f DB/postgres-config.yaml
kubectl apply -f DB/postgres-pvc-pv.yaml
kubectl apply -f DB/postgres-deployment.yaml

Rem Launch a pods able to act as consumer/producer with the cluster
kubectl apply -f Producer.yaml

Rem Wait for everything to be launched correctly
echo THE SCRIPT WILL WAIT FOR ALL POD TO BE READY THIS MAY TAKE A WHILE, YOU CAN CHECK THE STATUS OF THE PODS IN THE CMD WINDOWS THAT THE SCRIPT OPENED.
echo IF A POD HAS AN ERROR STATE KILL THE SCRIPT TO NOT WAIT 2H FOR TIMEOUT.
kubectl wait --for=condition=Ready pods --all --timeout=8040s

Rem Launch the Strimzi Operator instance
kubectl create -f "https://strimzi.io/install/latest?namespace=default"

Rem Wait for everything to be launched correctly
echo THE SCRIPT WILL WAIT FOR ALL POD TO BE READY THIS MAY TAKE A WHILE, YOU CAN CHECK THE STATUS OF THE PODS IN THE CMD WINDOWS THAT THE SCRIPT OPENED.
echo IF A POD HAS AN ERROR STATE KILL THE SCRIPT TO NOT WAIT 2H FOR TIMEOUT.
kubectl wait --for=condition=Ready pods --all --timeout=8040s

Rem Launch the Kafka cluster
kubectl apply -f Kafka/kafka-oauth-single.yaml


Rem Wait for the kafka cluster to be deployed correctly
kubectl wait kafka/my-cluster --for=condition=Ready --timeout=8040s

Rem Port forwarding to be able to reach pods from localhost
start cmd.exe /k kubectl port-forward svc/opa 8181:8181
start cmd.exe /k kubectl port-forward svc/postgres 5050:5432
start cmd.exe /k kubectl port-forward keycloak 8080