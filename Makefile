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
