#!/bin/bash
set -euo pipefail

# make sure that we are run from the project root
my_expected_name=setup.sh
my_actual_name=$0

if [[ "$my_expected_name" != "$my_actual_name" ]]; then
  echo "Please run me from the project root" >&2
  exit 1
fi

NO_CACHE=false

# check if environment setup
echo "Checking environment..."

# ensure .env exists
if [[ ! -f .env ]] ; then
  echo "  >> [add] .env"
  ./generate_dotenv.sh > .env
else
  echo "  >> [exists] .env"
fi

# build containers
if $NO_CACHE;
then
  echo "  >> [del] image"
  docker-compose rm --force --stop $SERVICE
  docker rmi --force $IMG || true
  echo "  >> [build] image --no-cache"
  docker-compose build --no-cache
else
  echo "  >> [build] image"
  docker-compose build
fi

docker-compose up -d --remove-orphans

# Setup Django
SERVICE=app
docker-compose run --rm $SERVICE /app/manage.py migrate
docker-compose run --rm $SERVICE /app/manage.py loaddata ./project/fixtures/admin.json

# print possible next steps
cat <<'EOF'
docker-compose logs -f
EOF