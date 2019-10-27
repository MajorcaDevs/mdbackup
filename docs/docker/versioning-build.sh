#!/bin/ash

set -e

function build_docs {
  #python -m venv .venv
  #. .venv/bin/activate

  pip install -r docs/requirements.txt
  mkdocs build --config-file=`ls mkdocs.y*ml` --site-dir=build/docs/$1

  #deactivate
  #rm -rf .venv

  jq ". |= .+ [{ \"title\": \"$1\", \"path\": \"$HOMEPAGE_URL/$1\" }]" build/docs/versions.json | sponge build/docs/versions.json
  echo "<script>window.app.version = '${1}'</script>" >> build/docs/$1/index.html
  echo "<script>window.app.homepage = '${HOMEPAGE_URL}'</script>" >> build/docs/$1/index.html
  echo "<script src=\"$HOMEPAGE_URL/version-menu.js\"></script>" >> build/docs/$1/index.html
}

git checkout -- .
# git clean -fdx .

mkdir -p build/docs
printf '[]' > build/docs/versions.json
cp docs/docker/version-menu.js build/docs
echo "<html><head></head><body><script>window.location='$HOMEPAGE_URL/stable/'</script></body></html>" > build/docs/index.html

python -m venv .venv
. .venv/bin/activate

echo Building docs for master branch
git checkout master
build_docs "stable"

echo Building docs for dev branch
git checkout dev
build_docs "dev"

for tag in `git tag | egrep '^v\d+\.\d+\.\d+$' | sort`; do
  git checkout $tag
  if [[ -d docs ]] && [[ -f docs/requirements.txt ]]; then
    echo Building docs for version $tag
    build_docs "${tag:1}"
  else
    echo Version $tag has no docs
  fi
done

if [[ ! -z "${BRANCH_NAME}" ]]; then
  git checkout $BRANCH_NAME
fi
