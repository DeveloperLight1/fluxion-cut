#!/usr/bin/env bash
# identifier: Password Brute Force
# description: Brute force password cracking using dictionary attack.

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
PasswordBruteForceHashPathQuery="Select a handshake file (.cap) for password cracking"
PasswordBruteForceDictionaryPathQuery="Select a wordlist file for brute force attack"
PasswordBruteForceStartingNotice="${CCyn}Password Brute Force$CClr attack starting..."
PasswordBruteForceCrackingNotice="Cracking password using aircrack-ng..."
PasswordBruteForceSuccessNotice="${CGrn}Success${CClr}: Password found!"
PasswordBruteForcePasswordFoundNotice="${CGrn}Password: $CClr"
PasswordBruteForceFailedNotice="${CRed}Failed${CClr}: Password not found in dictionary."
PasswordBruteForceCompletedTip="${CBCyn}Password Brute Force$CBYel attack completed.$CClr"
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# FLUXSCRIPT END

