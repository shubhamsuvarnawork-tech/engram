.PHONY: demo test up down install
install:        ## install backend deps
	cd backend && pip install -r requirements.txt
demo:           ## run the offline end-to-end demo (no services needed)
	cd backend && PYTHONPATH=. python -m app.seed.demo
test:           ## run the backend test suite
	cd backend && PYTHONPATH=. pytest
up:             ## bring up the full stack (postgres, neo4j, redis, api, web)
	docker compose up --build
down:
	docker compose down
