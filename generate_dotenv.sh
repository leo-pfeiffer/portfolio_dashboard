#!/bin/bash
set -euo pipefail

cat <<EOF
# Django
DJANGO_SECRET_KEY="alblg)!!b7er50q%oae)@d4nm8qm6bt#43moj(5hw46xk5iu)#"
DEBUG=1
DJANGO_PORT=8000

# Mail
MAIL_SMTP=
MAIL_EMAIL=
MAIL_PASSWORD=

# DegiroAPI
DEGIRO_USERNAME=
DEGIRO_PASSWORD=

# Database
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_PORT="5432"

EOF
