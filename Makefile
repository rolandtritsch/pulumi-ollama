SSH_KEY ?= ~/.ssh/ollama-key
OLLAMA_MODEL ?= qwen2.5-coder:0.5b

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

.PHONY: logs-bootstrap
logs-bootstrap: ## Follow bootstrap logs in CloudWatch
	@REGION=$$(pulumi config get aws:region); GROUP=$$(pulumi stack output BootstrapLogGroup); \
	aws logs tail "$$GROUP" --follow --region "$$REGION"

.PHONY: logs-ollama
logs-ollama: ## Follow Ollama logs in CloudWatch
	@REGION=$$(pulumi config get aws:region); GROUP=$$(pulumi stack output OllamaLogGroup); \
	aws logs tail "$$GROUP" --follow --region "$$REGION"

.PHONY: preview
preview: ## Preview the stack
	pulumi preview

.PHONY: test
test: ## Run unit and shell-rendering tests
	uv run python -m unittest discover -s tests -v

.PHONY: tunnel
tunnel: ## Open SSH tunnel to Ollama on localhost:11434
	@EIP=$$(pulumi stack output eipPublicIp); \
	echo "Tunneling localhost:11434 -> $$EIP:11434"; \
	ssh -N -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -L 11434:localhost:11434 -i $(SSH_KEY) ubuntu@$$EIP

.PHONY: up
up: ## Deploy the stack
	pulumi up --yes

.PHONY: verify
verify: ## Wait for Ollama and configured models to become ready
	uv run python scripts/verify.py
