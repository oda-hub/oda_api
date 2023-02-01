#!/bin/bash

set -ex 

echo ${level:=patch}

git checkout master
git pull origin master

git branch -D bump-release || echo "no patch branch yet"
git checkout -b bump-release

bump2version $level --verbose --commit --tag
bump2version release --verbose --commit --tag

new_version=$(< ./oda_api/pkg_info.json jq -r .version)

git branch -D bump-$new_version || echo "no patch branch yet"
git checkout -b bump-$new_version

git push origin bump-$new_version --force

python setup.py sdist bdist_wheel
twine upload $(ls -tr dist/*gz | tail -1) || true
twine upload $(ls -tr dist/*whl | tail -1) || true
