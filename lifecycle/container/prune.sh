#!/bin/bash
# Assemble a distroless rootfs at $OUT from the fully installed assemble stage.
#
# Inputs
#   $1          file listing the Debian packages to keep (comments allowed)
#   $2          file listing extra absolute paths to keep (comments allowed)
#   $3          file listing absolute paths to drop again (comments allowed)
#   OUT         target directory, defaults to /out
#
# Only the files owned by a kept package, plus the extra paths, end up in $OUT.
# /var/lib/dpkg/status.d  is written so scanners still see the exact packages
set -euo pipefail

# --- Inputs and helpers ---

OUT=${OUT:-/out}
KEEP_PKG_FILE=$1
KEEP_PATH_FILE=$2
DROP_PATH_FILE=${3:-/dev/null}

log() { echo "[prune] $*" >&2; }
strip_comments() { sed -e 's/#.*//' -e '/^[[:space:]]*$/d' -e 's/[[:space:]]*$//' "$1"; }
# Quote a path for use as a literal ERE. Without it the . in python3.14 matches
# any character, and a path holding + (libstdc++) is read as a quantifier.
ere_escape() { printf '%s' "$1" | sed 's/[][^$.*+?(){}|\]/\\&/g'; }

rm -rf "$OUT"
mkdir -p "$OUT"

# --- Files owned by the kept packages ---

KEEP_PKGS=$(strip_comments "$KEEP_PKG_FILE")
LIST=$(mktemp)
MISSING=""

for pkg in $KEEP_PKGS; do
    if ! dpkg-query -W "$pkg" >/dev/null 2>&1; then
        MISSING="$MISSING $pkg"
        continue
    fi
    dpkg-query -L "$pkg" >>"$LIST" 2>/dev/null
done
if [ -n "$MISSING" ]; then
    log "ERROR: kept packages are not installed:$MISSING"
    exit 1
fi

# --- Extra paths that no package owns ---

# $p is deliberately unquoted so an entry may be a glob, e.g. the multiarch
# /usr/lib/*/ossl-modules. A glob that matches nothing stays literal and is
# reported below, so no kept path can go missing without failing the build.
MISSING=""
while IFS= read -r p; do
    for m in $p; do
        if [ ! -e "$m" ] && [ ! -L "$m" ]; then
            MISSING="$MISSING $m"
            continue
        fi
        if [ -d "$m" ] && [ ! -L "$m" ]; then
            find "$m" >>"$LIST"
        else
            printf '%s\n' "$m" >>"$LIST"
        fi
    done
done < <(strip_comments "$KEEP_PATH_FILE")
if [ -n "$MISSING" ]; then
    log "ERROR: kept paths do not exist:$MISSING"
    exit 1
fi

# --- Drop filter ---

# Skip documentation, static archives, headers or build glue
DROP_RE='^/usr/share/(man|doc|info|lintian|bug|common-licenses|locale)(/|$)|\.a$|^/usr/include|/pkgconfig/'
# A caller drop that matches nothing is a typo or a stale version pin
MISSING_DROP=""
while IFS= read -r p; do
    esc="^$(ere_escape "$p")"
    grep -qE "$esc" "$LIST" || MISSING_DROP="$MISSING_DROP $p"
    DROP_RE="$DROP_RE|$esc"
done < <(strip_comments "$DROP_PATH_FILE")
if [ -n "$MISSING_DROP" ]; then
    log "ERROR: drop paths match nothing:$MISSING_DROP"
    exit 1
fi

grep -vE "$DROP_RE" "$LIST" | sort -u >"$LIST.f"

# --- Paths that no longer exist ---
# dpkg lists paths that the image build later deleted, tar aborts on those
while IFS= read -r p; do
    [ -e "$p" ] || [ -L "$p" ] || continue
    printf '%s\n' "$p"
done <"$LIST.f" >"$LIST"
rm -f "$LIST.f"
log "$(wc -l <"$LIST") paths selected"

# --- Copy the selected files ---
# tar preserves symlinks, hardlinks, modes and ownership
# --no-recursion is required, recursing undoes the drop filter
tar -cf - --no-recursion --files-from="$LIST" 2>/dev/null | tar -xf - -C "$OUT"

# --- Package database for scanners ---
mkdir -p "$OUT/var/lib/dpkg/status.d"
for pkg in $KEEP_PKGS; do
    dpkg-query -s "$pkg" >"$OUT/var/lib/dpkg/status.d/$pkg" 2>/dev/null
    arch=$(dpkg-query -W -f='${Architecture}' "$pkg")
    for cand in "/var/lib/dpkg/info/$pkg.md5sums" "/var/lib/dpkg/info/$pkg:$arch.md5sums"; do
        if [ -f "$cand" ]; then
            cp "$cand" "$OUT/var/lib/dpkg/status.d/$pkg.md5sums"
            break
        fi
    done
done
log "wrote $(ls "$OUT/var/lib/dpkg/status.d" | grep -cv '\.md5sums$') status.d entries"

# --- Directories no package owns ---
mkdir -p "$OUT/tmp" "$OUT/run" "$OUT/var/tmp" "$OUT/proc" "$OUT/sys" "$OUT/dev"
chmod 1777 "$OUT/tmp" "$OUT/var/tmp"

# --- Linker cache ---
ldconfig -r "$OUT"

# --- Top level staged separately ---
# /bin, /lib, /lib64 and /sbin are merged-usr symlinks
# COPY follows a symlink named as its source, so they are staged here and copied as directory contents
ROOTDIR="${OUT}-root"
rm -rf "$ROOTDIR"
mkdir -p "$ROOTDIR"
for entry in "$OUT"/*; do
    name=$(basename "$entry")
    if [ -L "$entry" ] || [ -f "$entry" ]; then
        mv "$entry" "$ROOTDIR/$name"
    fi
done
log "staged $(ls -A "$ROOTDIR" | tr '\n' ' ')in $ROOTDIR"
log "assembled $(du -sh "$OUT" | cut -f1)"
