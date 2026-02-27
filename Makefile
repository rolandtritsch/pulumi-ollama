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
	ssh -N -o ServerAliveInterval=30 -o ServerAliveCountMax=6 -L 11435:localhost:11434 -i ~/.ssh/aws-roland ubuntu@$$EIP

.PHONY: up
up: ## Deploy the stack
	pulumi up --yes
