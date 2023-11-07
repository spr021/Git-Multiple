#!/bin/bash

source config.env

options=()
num_options=0

# Read the .env file line by line
while IFS= read -r line; do
  # Skip empty lines and comments
  if [[ -n "$line" && "$line" != "#"* ]]; then
    IFS="=" read -r var_name var_value <<<"$line"
    if [[ "$var_name" == *USER* ]]; then
      options+=($var_value)
      num_options=$((num_options + 1))
    fi
  fi
done <"config.env"

if [ $num_options -eq 0 ]; then
  echo "No users found in config.env"
  echo "Add a user with the -a flag"
  exit 0
fi

CURRENT_USER=$(git config --global user.name)
options+=("Quit")
num_options=$((num_options + 1))
selected=0
VERSION="1.0.0"
Purple='\033[0;35m'
Green='\033[0;32m'
NC='\033[0m' # No Color

if [ $CURRENT_USER == "" ] && [ $num_options -eq 1 ]; then
  echo "No Git account found"
  echo "Add a user with the -a flag"
  exit 0
fi

display_version() {
  echo "switch $VERSION"
  exit 0
}

display_help() {
  echo "Usage: switch [OPTION]..."
  echo "Switch between Git accounts"
  echo ""
  echo "  -v, --version         display version"
  echo "  -h, --help            display help"
  echo ""
  echo "Report bugs to:"
  echo "https://github.com/spr021/Git-Multiple/issues"
  exit 0
}

add_user() {
  j=$((num_options + 1))
  echo "Adding new user"
  echo "Enter new user name: "
  read new_user
  echo "Enter new user email: "
  read new_email
  echo "New user: $new_user"
  echo "New email: $new_email"
  echo "Adding new user to config.env"
  echo "USER_$j=$new_user" >>config.env
  echo "EMAIL_$j=$new_email" >>config.env
  echo "New user added"
  exit 0
}

# Parse command line arguments
while true; do
  case "$1" in
  -v | --version)
    display_version
    shift
    ;;
  -h | --help)
    display_help
    shift
    ;;
  -a | --add)
    add_user
    shift 2
    ;;
  --)
    shift
    break
    ;;
  *) break ;;
  esac
done

# Function to display the menu
display_menu() {
  clear
  if [ "$CURRENT_USER" == "" ]; then
    echo "No Git account found"
    echo "Please select a user to set up Git"
    echo ""
  else
    echo -e "${Green}Current Git account: $CURRENT_USER${NC}"
  fi
  for ((i = 0; i < num_options; i++)); do
    if [ $i -eq $selected ]; then
      echo -e "${Purple}${options[i]}${NC}"
    else
      echo "${options[i]}"
    fi
  done
}

# Initial display of the menu
display_menu

# Loop for user input
while true; do
  read -rsn1 key
  case $key in
  "A") # Up arrow key
    selected=$(((selected - 1 + num_options) % num_options))
    display_menu
    ;;
  "B") # Down arrow key
    selected=$(((selected + 1) % num_options))
    display_menu
    ;;
  "") # Enter key
    for ((i = 0; i < num_options; i++)); do
      if [ $CURRENT_USER == "${options[i]}" ] && [ $i -eq $selected ]; then
        clear
        echo "Already using $CURRENT_USER Git account"
        exit 0
      fi
      if [ $selected -eq $((num_options - 1)) ]; then
        clear
        exit 0
      fi
      if [ $i -eq $selected ]; then
        j=$((i + 1))
        user_var="USER_$j"
        user_value="${!user_var}"
        email_var="EMAIL_$j"
        email_value="${!email_var}"
        git config --global user.name "$user_value"
        git config --global user.email "$email_value"
        clear
        echo "Switched to $user_value Git account"
        exit 0
      fi
    done
    ;;
  esac
done
