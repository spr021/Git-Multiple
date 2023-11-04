#!/bin/bash

source config.env

# Define an array of options
options=("$USER_1" "$USER_2")

# Check which Git account is currently set as global
CURRENT_USER=$(git config --global user.name)

options+=("Quit")
num_options=${#options[@]}
selected=0
Purple='\033[0;35m'
Green='\033[0;32m'
NC='\033[0m' # No Color

# Function to display the menu
display_menu() {
  clear
  echo -e "${Green}Current Git account: $CURRENT_USER${NC}"
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
