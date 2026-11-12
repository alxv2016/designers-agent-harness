#!/bin/bash
# The docs-authoring-and-sync script checks S1–S3 and S5–S14 (S4 is check_anchors.py, links are check_links.py), from
# the repo root, over docs/, the kit's .agents/HARNESS.md and every skill's references/.
#
#   bash .agents/skills/docs-authoring-and-sync/scripts/doc_checks.sh            # every doc, with baselines
#   bash .agents/skills/docs-authoring-and-sync/scripts/doc_checks.sh docs/X.md  # one or more docs, no baselines
#
# Each check prints its name, its hit count and — on a whole-docs run — its sanctioned baseline from the skill, then
# one line per hit; a whole-docs run over a baseline exits 1. Run it with bash: under zsh an unquoted file list does
# not split. The project name and doc prefix come from .agents/project.py.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
shopt -s nullglob

cfg() { python3 -c "import sys; sys.path.insert(0, '.agents'); import project; v = project.$1; print('\n'.join(v) if isinstance(v, (tuple, list)) else v)"; }
PROJECT_NAME=$(cfg PROJECT_NAME)
DOC_PREFIX=$(cfg DOC_PREFIX)
PROJECT_WIDE=$(cfg PROJECT_WIDE_DOCS)
GUIDE=docs/DOCUMENTATION_GUIDELINES.md

if [ $# -gt 0 ]; then
    DOCS=("$@")
    WITH_README=()
    WHOLE=0
else
    DESIGN_FILE=$(cfg DESIGN_FILE)
    DOCS=(docs/*.md .agents/HARNESS.md .agents/skills/*/references/*.md)
    [ -f "$DESIGN_FILE" ] && DOCS+=("$DESIGN_FILE")
    WITH_README=(README.md)
    WHOLE=1
fi

# check <id> <name> <baseline> <command…>: runs the command, counts its lines, prints them.
FAILED=0
check() {
    local id=$1 name=$2 base=$3
    shift 3
    local out n b
    out=$("$@" 2>/dev/null)
    n=$(printf '%s' "$out" | grep -c .)
    if [ "$WHOLE" = 1 ]; then
        printf '%s %s — %d hits (baseline %s)\n' "$id" "$name" "$n" "$base"
    else
        printf '%s %s — %d hits\n' "$id" "$name" "$n"
    fi
    [ -n "$out" ] && printf '%s\n' "$out" | sed 's/^/    /'
    b=${base%%[!0-9]*}
    if [ "$WHOLE" = 1 ] && [ -n "$b" ] && [ "$n" -gt "$b" ]; then
        printf '    FAIL — over the baseline of %s: a new hit to fix, or a baseline to move with its reason\n' "$b"
        FAILED=1
    fi
    return 0
}

is_wide() { printf '%s\n' "$PROJECT_WIDE" | grep -qxF "$1"; }
named() { case "$PROJECT_NAME" in "<"*|"") return 1 ;; *) return 0 ;; esac; }

# S1: every doc has a title. The project's own docs (prefixed, DESIGN.md and the kit's HARNESS.md) carry the project's title once
# PROJECT_NAME is set. A project-wide doc (GUIDELINES §3.1) names no project and links only to its siblings in docs/.
s1() {
    for f in "${DOCS[@]}"; do
        head -1 "$f" | grep -q '^# ' || { echo "$f: no title on line 1"; continue; }
        if is_wide "$f"; then
            named && grep -nF "$PROJECT_NAME" "$f" | sed "s|^|$f:|"
            awk '/^ *(```|~~~)/{c=!c;next} !c{gsub(/`[^`]*`/,"");print FNR":"$0}' "$f" | grep -E '\]\(\.\./' | sed "s|^|$f: links out of docs/:|"
        elif named && { [ "$f" = .agents/HARNESS.md ] || [ "$f" = "$(cfg DESIGN_FILE)" ] || { [ -n "$DOC_PREFIX" ] && case "$f" in docs/"$DOC_PREFIX"_*) true ;; *) false ;; esac; }; }; then
            head -1 "$f" | grep -qF "# $PROJECT_NAME — " || echo "$f: title is not '# $PROJECT_NAME — <Topic>'"
        fi
    done
}
s2() { for f in "${DOCS[@]}"; do [ "$(wc -l < "$f")" -gt 150 ] && ! grep -q '^| § | Section | Look here for |' "$f" && echo "$f"; done; }
s3() {
    for f in "${DOCS[@]}"; do
        case "$f" in .agents/skills/*/references/*) continue ;; esac  # a reference may continue its skill's numbering
        awk -v F="$f" '/^ *```/{c=!c;next} c{next} /^## [0-9]+\. /{split($2,a,".");n=a[1]+0;if(n!=t+1)printf "%s:%d: ## %d after %d\n",F,NR,n,t;t=n;s=0;next} /^### [0-9]+\.[0-9]+ /{split($2,a,".");if(a[1]+0!=t)printf "%s:%d: ### %s under ## %d\n",F,NR,$2,t;else if(a[2]+0!=s+1)printf "%s:%d: ### %s after %d.%d\n",F,NR,$2,t,s;s=a[2]+0}' "$f"
    done
}
s5() { awk 'FNR==1{o=""} /^ *(```+|~~~+)/{match($0,/^ *(```+|~~~+)/);f=substr($0,RSTART,RLENGTH);gsub(/ /,"",f);r=substr($0,RSTART+RLENGTH);if(o==""){o=f;if(r~/^[[:space:]]*$/)printf "%s:%d\n",FILENAME,FNR}else if(f==o&&r~/^[[:space:]]*$/)o=""}' "${DOCS[@]}" "${WITH_README[@]}"; }
s6() { awk 'FNR==1{p="";c=0;h=0} /^ *```/{c=!c} !c&&h&&FNR==h+1{if($0==""||$0~/^ *([-*+]|[0-9]+\.|\|) /)printf "%s:%d: %s\n",FILENAME,h,l;h=0} !c&&p==""&&/^(\*\*|__)[^*_].*(\*\*|__)$/&&$0!~/[.,;:!?](\*\*|__)$/{h=FNR;l=$0} {p=$0}' "${DOCS[@]}" "${WITH_README[@]}"; }
s7() { grep -niE "\b(used to (be|draw|run|call|use|live|sit|show)|formerly|originally|until recently|previously|closed on 20[0-9]{2}|(since|until) 20[0-9]{2}-[0-9]{2}-[0-9]{2}|was (changed|renamed|replaced|removed|reverted|fixed)|changed from|we tried|it turned out|after investigating)\b" "${DOCS[@]}" | grep -v "^$GUIDE:"; }
s8() { grep -niE "\b(note that|it'?s worth (mentioning|noting)|in order to|simply|basically|needless to say|it should be noted|as above|as mentioned (above|earlier|before)|the earlier table|the table above)\b" "${DOCS[@]}" | grep -v "^$GUIDE:"; }
s9() {
    for f in "${DOCS[@]}"; do
        awk '/^ *```/{c=!c;next} !c' "$f" | sed 's/`[^`]*`//g' | grep -oE '\[[A-Z?!]{1,5}\]([^(]|$)' | sed -E 's/^(\[[^]]*\]).*/\1/' | sort -u | while IFS= read -r t; do
            grep -qF "| \`$t\` |" "$f" || echo "$f: $t"
        done
    done
}
s10() { awk 'FNR==1{o="";g=""} /^ *(```+|~~~+)/{match($0,/^ *(```+|~~~+)/);m=substr($0,RSTART,RLENGTH);gsub(/ /,"",m);r=substr($0,RSTART+RLENGTH);if(o==""){o=m;g=r;gsub(/[[:space:]]/,"",g)}else if(length(m)>=length(o)&&substr(m,1,1)==substr(o,1,1)&&r~/^[[:space:]]*$/){o="";g=""};next} (o==""||g=="")&&/[┌┐└┘├┤┬┴┼─│═║╔╗╚╝]|\+-{3,}|-{2,}>|<-{2,}/{printf "%s:%d: %s\n",FILENAME,FNR,substr($0,1,100)}' "${DOCS[@]}" "${WITH_README[@]}"; }
s11() { awk 'FNR==1{m=0} /^ *```mermaid/{m=1;next} m&&/^ *```/{m=0} m&&/^[[:space:]]*(style|classDef|class|linkStyle)[[:space:]]/{printf "%s:%d\n",FILENAME,FNR}' "${DOCS[@]}"; }
s12() { grep -nE '#L[0-9]+|\.(c|cc|cpp|h|hpp|py|js|jsx|ts|tsx|mjs|vue|svelte|css|scss|swift|kt|java|go|rs|rb|dart|cs)(:|#L)[0-9]+|\b[Ll]ine [0-9]+ (of|in)\b|\b[Ll]ines [0-9]+ ?[-–] ?[0-9]+\b' "${DOCS[@]}" "${WITH_README[@]}"; }
s13() { for f in "${DOCS[@]}"; do case "$f" in docs/*) grep -q "](docs/$(basename "$f"))" README.md || echo "$f" ;; esac; done; }
s14() { awk 'function o(){if(n!=""&&w>600&&!t)printf "%s: %d words: %s\n",F,w,substr(n,1,70)} FNR==1{o();F=FILENAME;n="";w=0;t=0;c=0} /^ *```/{c=!c} !c&&/^#{2,4} /{o();n=$0;w=0;t=0;next} /^\|/{t=1} {w+=NF} END{o()}' "${DOCS[@]}"; }

check S1 "Title" 0 s1
check S2 "Contents table" 0 s2
check S3 "Numbering" 0 s3
check S5 "Fence without a language" 0 s5
check S6 "Bold paragraph as a heading" 0 s6
check S7 "History words (read for plain 'was' too)" 0 s7
check S8 "Filler and 'as above'" 0 s8
check S9 "Tag used but not in the legend" 0 s9
check S10 "ASCII art outside a fenced language block" 0 s10
check S11 "style/classDef in Mermaid" 0 s11
check S12 "Line-number references" 0 s12
check S13 "Doc missing from README" 0 s13
check S14 "Section over 600 words with no table or subheading" 0 s14
echo "S4 contents rows, anchors and § citations: python3 $(dirname "$0")/check_anchors.py"
echo "S15 links: python3 $(dirname "$0")/check_links.py"
exit "$FAILED"
