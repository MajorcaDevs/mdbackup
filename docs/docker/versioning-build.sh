#!/bin/ash

set -e

function build_docs {
  #python -m venv .venv
  #. .venv/bin/activate

  pip install -r docs/requirements.txt
  mkdocs build --config-file=`ls mkdocs.y*ml` --site-dir=build/docs/$1

  #deactivate
  #rm -rf .venv

  jq ". |= .+ [\"$1\"]" build/docs/versions.json | sponge build/docs/versions.json
}

git checkout -- .
git clean -fdx .

mkdir -p build/docs
printf '[]' > build/docs/versions.json

python -m venv .venv
. .venv/bin/activate

echo Building docs for dev branch
git checkout dev
build_docs "dev"

echo Building docs for master branch
git checkout master
build_docs "latest"

for tag in `git tag | egrep '^v\d+\.\d+\.\d+$' | sort`; do
  git checkout $tag
  if [[ -d docs ]]; then
    echo Building docs for version $tag
    build_docs "${tag:1}"
  else
    echo Version $tag has no docs
  fi
done

if [[ ! -z "${BRANCH_NAME}" ]]; then
  git checkout $BRANCH_NAME
fi
