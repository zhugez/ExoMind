.PHONY: doctor index recall serve mcp bootstrap

doctor:
	cargo run --bin exom -- doctor --notes-root . --graph .neural/graph.json

index:
	cargo run --bin exom -- index --notes-root . --out-root .neural

recall:
	cargo run --bin exom -- recall --query "$(Q)" --topk $${K:-10} --graph .neural/graph.json

bootstrap:
	bash scripts/bootstrap.sh
