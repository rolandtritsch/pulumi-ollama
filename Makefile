.PHONY: bash
bash: ## SSH into the instance
	@EIP=$$(pulumi stack output eipPublicIp); \
	ssh -i ~/.ssh/aws-roland ubuntu@$$EIP

.PHONY: destroy
destroy: ## Tear down the stack
	pulumi destroy --yes

.PHONY: help
help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-15s %s\n", $$1, $$2}'

.PHONY: ollama
ollama: ## Start ollama client against localhost:11435
	OLLAMA_HOST=http://localhost:11435 ollama run qwen3-coder-next:q4_K_M

.PHONY: preview
preview: ## Preview the stack
	pulumi preview

.PHONY: tunnel
tunnel: ## Open SSH tunnel to Ollama on localhost:11435
	@EIP=$$(pulumi stack output eipPublicIp); \
	echo "Tunneling localhost:11435 -> $$EIP:11434"; \
	ssh -N -L 11435:localhost:11434 -i ~/.ssh/aws-roland ubuntu@$$EIP

.PHONY: up
up: ## Deploy the stack
	pulumi up --yes
