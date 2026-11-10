TOPO := sp-lab.clab.yml
PY   := python3

.PHONY: help prep deploy destroy check test failover backup inspect lint

help:
	@echo "make prep      - carga modulos del kernel (MPLS, VRF, VXLAN) en el host"
	@echo "make deploy    - despliega el laboratorio"
	@echo "make check     - health check del plano de control"
	@echo "make test      - pruebas de plano de control y servicios"
	@echo "make failover  - pruebas de fallas simuladas"
	@echo "make backup    - respaldo de configuraciones + diff (TICKET=CHG-0001)"
	@echo "make destroy   - elimina el laboratorio"

prep:
	sudo ./scripts/host-prep.sh

deploy: prep
	sudo containerlab deploy -t $(TOPO)

destroy:
	sudo containerlab destroy -t $(TOPO) --cleanup

inspect:
	sudo containerlab inspect -t $(TOPO)

check:
	$(PY) automation/health_check.py

test:
	$(PY) -m pytest -v

failover:
	$(PY) -m pytest -v -m failover -s

backup:
	$(PY) automation/backup_configs.py $(if $(TICKET),--ticket $(TICKET),)

lint:
	yamllint -d relaxed $(TOPO) .github/workflows
	$(PY) -m py_compile automation/*.py tests/*.py
	shellcheck -s sh configs/*/setup.sh scripts/*.sh
