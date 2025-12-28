#!/usr/bin/env bash
# identifier: Password Brute Force
# description: Перебор паролей с помощью словарной атаки.

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
PasswordBruteForceHashPathQuery="Выберите файл handshake (.cap) для перебора паролей"
PasswordBruteForceDictionaryPathQuery="Выберите файл словаря для атаки перебора"
PasswordBruteForceStartingNotice="Запуск атаки ${CCyn}Перебор паролей$CClr..."
PasswordBruteForceCrackingNotice="Подбор пароля с помощью aircrack-ng..."
PasswordBruteForceSuccessNotice="${CGrn}Успех${CClr}: Пароль найден!"
PasswordBruteForcePasswordFoundNotice="${CGrn}Пароль: $CClr"
PasswordBruteForceFailedNotice="${CRed}Неудача${CClr}: Пароль не найден в словаре."
PasswordBruteForceCompletedTip="${CBCyn}Перебор паролей$CBYel завершен.$CClr"
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# FLUXSCRIPT END

