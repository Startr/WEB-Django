help: 
	@echo "================================================"
	@echo "       Startr/WEB-Django by Startr.Cloud"
	@echo "================================================"
	@echo "This is the default make command."
	@echo "This command lists available make commands."
	@echo ""
	@echo "Usage example:"
	@echo "    make it_run"
	@echo ""
	@echo "Available make commands:"
	@echo ""
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | \
		awk -v RS= -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data base/ { \
		if ($$1 !~ "^[#.]") {print $$1}}' | \
		sort | \
		grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'
	@echo ""

# Docker container name
CONTAINER = web-django-develop

# Django management commands
bash:
	docker exec -it $(CONTAINER) bash

django:
	@if [ "$(cmd)" = "" ]; then \
		echo "Usage: make django cmd='command'"; \
		echo "Example: make django cmd='migrate'"; \
	else \
		docker exec -it $(CONTAINER) bash -c "\
			cd /project/our_site && \
			python manage.py $(cmd)"; \
	fi

setup_groups:
	docker exec -it $(CONTAINER) bash -c "\
		cd /project/our_site && \
		python manage.py setup_groups"

it_run:
	@bash -c 'bash <(curl -sL startr.sh) run'

it_build:
	@bash -c 'bash <(curl -sL startr.sh) build'

it_startr:
	# @bash -c 'fswatch -r -v -e ".*" ./our_site/django_startr/ | while read changed_path; do \
	# 	echo "Detected change in $$changed_path"; \
	# 	git restore ./our_site/experiences/ && git clean -fd ./our_site/experiences/; \
	# 	docker exec -it web-django-develop bash -c "cd /project/our_site && ./manage.py startr experiences && ./manage.py runserver 0.0.0.0:8000"; \
	# done'
	git restore ./our_site/experiences/ && git clean -fd ./our_site/experiences/; \
	docker exec -it web-django-develop bash -c "cd /project/our_site && ./manage.py startr experiences && ./manage.py runserver 0.0.0.0:8000";

update_submodules:
	@echo "Developer instructions: Please update your Dockerfile manually to add the appropriate 'RUN' command for installing git (using apt-get or apk) and to include the submodule update command. Then run 'git submodule update --init --recursive'."

# Check if .gitmodules exists (returns 1 if present, empty otherwise)
HAS_SUBMODULE := $(shell [ -f .gitmodules ] && echo 1)

deploy:
	@if [ "$(HAS_SUBMODULE)" = "1" ]; then \
		echo "Submodules detected."; \
		echo "Instead of using the default 'caprover deploy' command,";\
		echo "we will create a tar of the project and deploy it"; \
		echo "Creating tar of project..."; \
		git ls-files --recurse-submodules | tar -czf deploy.tar -T -; \
		echo "Deploying to CapRover using the tar file..."; \
		npx caprover deploy -t ./deploy.tar; \
		rm ./deploy.tar; \
	else \
		echo "No submodules detected. Deploying normally..."; \
		npx caprover deploy; \
	fi

minor_release:
	# Start a minor release with incremented minor version
	git flow release start $$(git tag --sort=-v:refname | sed 's/^v//' | head -n 1 | awk -F'.' '{print $$1"."$$2+1".0"}')

patch_release:
	# Start a patch release with incremented patch version
	git flow release start $$(git tag --sort=-v:refname | sed 's/^v//' | head -n 1 | awk -F'.' '{print $$1"."$$2"."$$3+1}')

major_release:
	# Start a major release with incremented major version
	git flow release start $$(git tag --sort=-v:refname | sed 's/^v//' | head -n 1 | awk -F'.' '{print $$1+1".0.0"}')

hotfix:
	# Start a hotfix with incremented patch version
	git flow hotfix start $$(git tag --sort=-v:refname | sed 's/^v//' | head -n 1 | awk -F'.' '{print $$1"."$$2"."$$3+1}')

release_finish:
	git flow release finish "$$(git branch --show-current | sed 's/release\///')" && git push origin develop && git push origin master && git push --tags && git checkout develop

hotfix_finish:
	git flow hotfix finish "$$(git branch --show-current | sed 's/hotfix\///')" && git push origin develop && git push origin master && git push --tags && git checkout develop

things_clean:
	git clean --exclude=!.env -Xdf
