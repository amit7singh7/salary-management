.PHONY: seed run test bench
seed:  ; cd backend && python seed.py --reset
run:   ; cd backend && python run.py
test:  ; cd backend && python -m unittest discover -s . -t . -p "test_*.py"
bench: ; cd backend && python benchmark.py
