#!/bin/bash

function my_readlink() {
    cd "$1" || exit 1
    pwd
    cd - > /dev/null || exit 1
}

function cat_readme() {
    echo ""
    echo "Usage: $(basename "$0") [-i] DELIVERY_DIR REPORTS_DIR"
    echo -e "\t-i\t\tDownload the Docker image"
    echo -e "\tDELIVERY_DIR\tShould be the directory where your project files are"
    echo -e "\tREPORTS_DIR\tShould be the directory where we output the reports"
    echo -e "\t\t\tTake note that existing reports will be overridden"
    echo ""
}

function strrep() {
    local string="$1"
    local count="$2"
    local result=""

    for ((i = 0; i < count; i++)); do
        result="${result}${string}"
    done
    echo "$result"
}

download_image=false

# Check for the presence of the -i flag
if [[ "$*" == *"-i"* ]]; then
    download_image=true
    # Remove the -i flag from the list of parameters
    set -- "${@//"-i"}"
fi

if [ $# -ge 2 ]; then
    DELIVERY_DIR=$(my_readlink "$1")
    REPORTS_DIR=$(my_readlink "$2")
    DOCKER_SOCKET_PATH=/var/run/docker.sock
    HAS_SOCKET_ACCESS=$(test -r $DOCKER_SOCKET_PATH; echo "$?")
    GHCR_REGISTRY_TOKEN=$(curl -s "https://ghcr.io/token?service=ghcr.io&scope=repository:epitech/coding-style-checker:pull" | grep -o '"token":"[^"]*' | grep -o '[^"]*$') 
    GHCR_REPOSITORY_STATUS=$(curl -I -f -s -o /dev/null -H "Authorization: Bearer $GHCR_REGISTRY_TOKEN" "https://ghcr.io/v2/epitech/coding-style-checker/manifests/latest" && echo 0 || echo 1)
    BASE_EXEC_CMD="docker"
    EXPORT_FILE="$REPORTS_DIR"/coding-style-reports.log
    ### delete existing report file
    rm -f "$EXPORT_FILE"

    ### Pull new version of docker image and clean olds

    if [ "$download_image" = true ]; then
        if [ $HAS_SOCKET_ACCESS -ne 0 ]; then
            echo "WARNING: Socket access is denied"
            echo "To fix this we will add the current user to docker group with : sudo usermod -a -G docker $USER"
            read -p "Do you want to proceed? (yes/no) " yn
            case $yn in 
                yes | Y | y | Yes | YES) echo "ok, we will proceed";
                    sudo usermod -a -G docker $USER;
                    echo "You must reboot your computer for the changes to take effect";;
                no | N | n | No | NO) echo "ok, Skipping";;
                * ) echo "invalid response, Skipping";;
            esac
            BASE_EXEC_CMD="sudo ${BASE_EXEC_CMD}"
        fi
        if [ $GHCR_REPOSITORY_STATUS -eq 0 ]; then
            echo "Downloading new image and cleaning old one..."
            $BASE_EXEC_CMD pull ghcr.io/epitech/coding-style-checker:latest && $BASE_EXEC_CMD image prune -f
            echo "Download OK"
        else
            echo "WARNING: Skipping image download"
        fi
    fi

    ### generate reports
    sudo $BASE_EXEC_CMD run --rm -i -v "$DELIVERY_DIR":"/mnt/delivery" -v "$REPORTS_DIR":"/mnt/reports" ghcr.io/epitech/coding-style-checker:latest "/mnt/delivery" "/mnt/reports"
    [[ -f "$EXPORT_FILE" ]] && echo "$(wc -l < "$EXPORT_FILE") coding style error(s) reported in "$EXPORT_FILE", $(grep -c ": MAJOR:" "$EXPORT_FILE") major, $(grep -c ": MINOR:" "$EXPORT_FILE") minor, $(grep -c ": INFO:" "$EXPORT_FILE") info"


    # This is the "improve" part
    BESTLEN=0
    while IFS= read -r LINE; do
        WORD=$(echo $LINE | cut -d' ' -f1);
        LEN=${#WORD}
        if [ $LEN -gt $BESTLEN ]; then
            BESTLEN=$LEN
        fi
    done < "$EXPORT_FILE"

    while IFS= read -r LINE; do
        WORD=$(echo $LINE | cut -d' ' -f1);
        LEN=${#WORD}
        LINE="${LINE:$LEN}"
        REP=$(strrep "\x20" $((BESTLEN - LEN + 4)))
        echo -n $WORD
        echo -ne $REP;
        echo $LINE | sed -e 's/MINOR/\x1b[2D\x1b[34;1m▼ \x1b[m/g' -e 's/MAJOR/\x1b[2D\x1b[31;1m▲ \x1b[m/g' -e 's/INFO/\x1b[2D\x1b[35;1m# \x1b[m/g'
    done < "$EXPORT_FILE"

    rm -f "$EXPORT_FILE"
else
    cat_readme
fi
