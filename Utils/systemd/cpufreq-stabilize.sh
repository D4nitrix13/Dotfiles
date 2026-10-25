#!/usr/bin/env bash
# Apply a conservative cpufreq policy during system startup.
#
# This is a mitigation for a saturated heatsink on the Dell Inspiron 15 3535,
# not a repair for the cooling hardware. It limits the Ryzen 7 7730U to 3.0 GHz
# and uses the powersave governor with the balance_power energy preference.

set -euo pipefail

apply() {
  local pattern="$1" value="$2" file

  # The path pattern is a fixed sysfs glob and intentionally undergoes word splitting.
  # shellcheck disable=SC2086
  for file in ${pattern}; do
    if [[ -w "${file}" ]]; then
      echo "${value}" > "${file}" 2>/dev/null || true
    fi
  done
}

apply "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor" "powersave"
apply "/sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq" "3000000"
apply "/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference" "balance_power"
