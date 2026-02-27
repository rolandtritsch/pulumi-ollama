.PHONY: destroy help up

destroy: ## Tear down the stack
	pulumi destroy --yes

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-15s %s\n", $$1, $$2}'

up: ## Deploy the stack
	pulumi up --yes
