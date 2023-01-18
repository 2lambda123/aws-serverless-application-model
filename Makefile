CFN_SCHEMA_VERSION = v7.2.3
CFN_SCHEMA_PATH = .tmp/cloudformation-$(CFN_SCHEMA_VERSION).schema.json

target:
	$(info ${HELP_MESSAGE})
	@exit 0

init:
	pip install -e '.[dev]'

test:
	AWS_DEFAULT_REGION=us-east-1 pytest --cov samtranslator --cov-report term-missing --cov-fail-under 95 -n auto tests/*

test-fast:
	pytest -x --cov samtranslator --cov-report term-missing --cov-fail-under 95 -n auto tests/*

test-cov-report:
	pytest --cov samtranslator --cov-report term-missing --cov-report html --cov-fail-under 95 tests/*

integ-test:
	pytest --no-cov integration/*

black:
	black setup.py samtranslator/* tests/* integration/* bin/*.py
	bin/json-format.py --write tests integration samtranslator/policy_templates_data
	bin/yaml-format.py --write tests
	bin/yaml-format.py --write integration --add-test-metadata

black-check: get-cfn-schema
	# Checking latest schema was generated (run `make schema` if this fails)
	mkdir -p .tmp
	python samtranslator/schema/schema.py --sam-schema .tmp/sam.schema.json --cfn-schema $(CFN_SCHEMA_PATH) --unified-schema .tmp/unified.schema.json
	diff -u samtranslator/schema/schema.json .tmp/sam.schema.json
	diff -u samtranslator/schema/unified.schema.json .tmp/unified.schema.json
	black --check setup.py samtranslator/* tests/* integration/* bin/*.py
	bin/json-format.py --check tests integration samtranslator/policy_templates_data
	bin/yaml-format.py --check tests
	bin/yaml-format.py --check integration --add-test-metadata

lint:
	# mypy performs type check
	mypy --strict samtranslator bin
	# Linter performs static analysis to catch latent bugs
	pylint --rcfile .pylintrc samtranslator
	# cfn-lint to make sure generated CloudFormation makes sense
	bin/run_cfn_lint.sh

prepare-companion-stack:
	pytest -v --no-cov integration/setup -m setup

get-cfn-schema:
	mkdir -p .tmp
	test -f $(CFN_SCHEMA_PATH) || curl -o $(CFN_SCHEMA_PATH) https://raw.githubusercontent.com/awslabs/goformation/$(CFN_SCHEMA_VERSION)/schema/cloudformation.schema.json

schema: get-cfn-schema
	python samtranslator/schema/schema.py --sam-schema samtranslator/schema/schema.json --cfn-schema $(CFN_SCHEMA_PATH) --unified-schema samtranslator/schema/unified.schema.json

# Command to run everytime you make changes to verify everything works
dev: test

# Verifications to run before sending a pull request
pr: black-check lint init dev

clean:
	rm -r .tmp

define HELP_MESSAGE

Usage: $ make [TARGETS]

TARGETS
	init        Initialize and install the requirements and dev-requirements for this project.
	test        Run the Unit tests.
	integ-test  Run the Integration tests.
	dev         Run all development tests after a change.
	pr          Perform all checks before submitting a Pull Request.
	prepare-companion-stack    Create or update the companion stack for running integration tests.

endef
