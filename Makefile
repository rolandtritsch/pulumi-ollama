.PHONY: destroy help tunnel up

destroy: ## Tear down the stack
	pulumi destroy --yes

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-15s %s\n", $$1, $$2}'

preview: ## Preview the stack
	pulumi preview

tunnel: ## Open SSH tunnel to Ollama on localhost:11435
	@EIP=$$(pulumi stack output eipPublicIp); \
	echo "Tunneling localhost:11435 -> $$EIP:11434"; \
	ssh -N -L 11435:localhost:11434 -i ~/.ssh/aws-roland ubuntu@$$EIP

up: ## Deploy the stack
	pulumi up --yes
