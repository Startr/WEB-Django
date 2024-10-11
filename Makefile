help: 
	@echo ""
	@echo "Startr/WEB-Django by Startr.Cloud"
	@echo ""
	@echo "This is the default make command."
	@echo "This command lists available make commands."
	@echo ""
	@echo "Usage example:"
	@echo "    make it_run"
	@echo ""
	@echo "Available make commands:"
	@echo ""
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'
	@echo ""

it_run:
	@bash -c 'bash <(curl -sL startr.sh) run'

it_build:
	@bash -c 'bash <(curl -sL startr.sh) build'
