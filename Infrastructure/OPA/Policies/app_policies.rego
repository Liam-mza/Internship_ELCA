package app.authz

import future.keywords

default is_admin := false

is_admin if {
	s := "admin"
	inputtab := [input.topic, s]
	test := concat("_", inputtab)
	users := object.get(data.topics, test, "None")
	input.name in users
}