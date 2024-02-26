package kafka.authz

import future.keywords

default allow := false

allow if {
	input.action.resourcePattern.resourceType in ["TOPIC"]
	input.action.operation in ["READ", "DESCRIBE"]
	is_consumer
}

allow if {
	input.action.resourcePattern.resourceType in ["TOPIC"]
	input.action.operation in ["WRITE", "READ", "DESCRIBE", "CREATE"]
	is_producer
}

allow if {
	input.action.resourcePattern.resourceType in ["TOPIC", "CLUSTER"]
	input.action.operation in [
		"READ", "WRITE", "CREATE", "DELETE", "ALTER", "DESCRIBE", "IDEMPOTENT_WRITE",
		"DescribeConfigs", "AlterConfigs",
	]
	is_admin
}

##########################################################
# Function to authorize actions required by kafka protocol
##########################################################
allow if {
	input.action.resourcePattern.resourceType in ["CLUSTER"]
	input.action.operation in ["IDEMPOTENT_WRITE"]
}

allow if {
	input.action.resourcePattern.resourceType in ["GROUP"]
	input.action.operation in ["DESCRIBE", "READ"]
}

#########################################################

is_admin if {
	s := "admin"
	inputtab := [input.action.resourcePattern.name, s]
	test := concat("_", inputtab)
	users := object.get(data.topics, test, "None")
	input.requestContext.principal.name in users
}

is_consumer if {
	s := "consumer"
	inputtab := [input.action.resourcePattern.name, s]
	test := concat("_", inputtab)
	users := object.get(data.topics, test, "None")
	input.requestContext.principal.name in users
}

is_producer if {
	s := "producer"
	inputtab := [input.action.resourcePattern.name, s]
	test := concat("_", inputtab)
	users := object.get(data.topics, test, "None")
	input.requestContext.principal.name in users
}
