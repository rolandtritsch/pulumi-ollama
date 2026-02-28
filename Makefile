OLLAMA_MODEL ?= qwen3-coder:30b

.PHONY: instance-bash
bash: ## SSH into the instance
	@EIP=$$(pulumi stack output eipPublicIp); \
	ssh -i ~/.ssh/aws-roland ubuntu@$$EIP

.PHONY: stack-destroy
destroy: ## Tear down the stack
	pulumi destroy --yes

.PHONY: help
help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-15s %s\n", $$1, $$2}'

.PHONY: instance-start
instance-start: ## Start the EC2 instance
	@ID=$$(pulumi stack output instanceId); \
	echo "Starting $$ID ..."; \
	AWS_PROFILE=roland aws ec2 start-instances --instance-ids $$ID --region eu-west-1

.PHONY: instance-stop
instance-stop: ## Stop the EC2 instance
	@ID=$$(pulumi stack output instanceId); \
	echo "Stopping $$ID ..."; \
	AWS_PROFILE=roland aws ec2 stop-instances --instance-ids $$ID --region eu-west-1

.PHONY: ollama-codex
ollama-codex: ## Start an ollama codex client
	ollama launch codex --model $(OLLAMA_MODEL)

.PHONY: ollama-list
ollama-list: ## List the available ollama models
	ollama list

.PHONY: ollama-run
ollama-run: ## List the available ollama models
	ollama run $(OLLAMA_MODEL)

.PHONY: stack-preview
preview: ## Preview the stack
	pulumi preview

.PHONY: instance-tunnel
tunnel: ## Open SSH tunnel to Ollama on localhost:11434
	@EIP=$$(pulumi stack output eipPublicIp); \
	echo "Note: Run 'sudo systemctl stop ollama' first"; \
	echo "Tunneling localhost:11434 -> $$EIP:11434"; \
	ssh -N -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -L 11434:localhost:11434 -i ~/.ssh/aws-roland ubuntu@$$EIP

.PHONY: stack-up
up: ## Deploy the stack
	pulumi up --yes
