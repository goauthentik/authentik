_completions () {
	if [[ -z "${MIGRATE_PATH}" ]];
	then MIGRATE_PATH="./";
	else MIGRATE_PATH="${MIGRATE_PATH}"; fi

	if [[ -z "${TMP_STRUCTURE_PATH}" ]];
	then TMP_STRUCTURE_PATH="./tmp/";
	else TMP_STRUCTURE_PATH="${TMP_STRUCTURE_PATH}"; fi

	if [[ $1 = $3 ]];
	then LSPATH="$MIGRATE_PATH";
	else LSPATH="$TMP_STRUCTURE_PATH"; fi

	for i in $(compgen -f -- "$LSPATH$2" | cut -d "/" -f 2-); do
		if [[ -d "$LSPATH$i" ]];
		then COMPREPLY+=("$i/");
		else COMPREPLY+=("$i"); fi
	done
}

complete -o nospace -o filenames -F _completions map
