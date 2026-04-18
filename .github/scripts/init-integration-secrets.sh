#!/usr/bin/env bash

set -euo pipefail

require_env() {
  local var_name="$1"
  if [[ -z "${!var_name:-}" ]]; then
    echo "::error::Missing secret/env ${var_name}"
    exit 1
  fi
}

write_secret_file() {
  local var_name="$1"
  local target_path="$2"

  require_env "$var_name"

  mkdir -p "$(dirname "$target_path")"
  printf '%s\n' "${!var_name}" > "$target_path"
  chmod 600 "$target_path"
}

write_secret_file "GATEWAY_BASE_CREDS" "Gateway/cmd/base.creds"
write_secret_file "TEST_CREDS" "Gateway/cmd/admin_test.creds"
write_secret_file "TEST_CREDS" "DataConsumer/cmd/admin_test.creds"
write_secret_file "DATA_CONSUMER_CREDS" "DataConsumer/cmd/data_consumer.creds"
write_secret_file "TEST_CREDS" "Dashboard/backend/admin_test.creds"
write_secret_file "DASHBOARD_CREDS" "Dashboard/backend/dashboard.creds"
write_secret_file "TEST_CREDS" "systemTests/admin_test.creds"

echo "Credentials initialized successfully."