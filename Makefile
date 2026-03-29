SSH_KEY ?= ~/.ssh/ollama-key
OLLAMA_MODEL ?= llama3.2:latest

.PHONY: bash
bash: ## SSH into the instance
	@EIP=$$(pulumi stack output eipPublicIp); \
	ssh -i $(SSH_KEY) ubuntu@$$EIP

.PHONY: destroy
destroy: ## Tear down the stack
	pulumi destroy --yes

.PHONY: help
help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-15s %s\n", $$1, $$2}'

.PHONY: instance-start
instance-start: ## Start the EC2 instance
	@ID=$$(pulumi stack output instanceId); \
	echo "Starting $$ID ..."; \
	aws ec2 start-instances --instance-ids $$ID

.PHONY: instance-stop
instance-stop: ## Stop the EC2 instance
	@ID=$$(pulumi stack output instanceId); \
	echo "Stopping $$ID ..."; \
	aws ec2 stop-instances --instance-ids $$ID

.PHONY: ollama-list
ollama-list: ## List the available ollama models
	ollama list

.PHONY: ollama-run
ollama-run: ## Run an ollama model interactively
	ollama run $(OLLAMA_MODEL)

.PHONY: preview
preview: ## Preview the stack
	pulumi preview

.PHONY: tunnel
tunnel: ## Open SSH tunnel to Ollama on localhost:11434
	@EIP=$$(pulumi stack output eipPublicIp); \
	echo "Tunneling localhost:11434 -> $$EIP:11434"; \
	ssh -N -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -L 11434:localhost:11434 -i $(SSH_KEY) ubuntu@$$EIP

.PHONY: up
up: ## Deploy the stack
	pulumi up --yes
