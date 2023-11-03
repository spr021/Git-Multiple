#!/bin/bash

source config.env

# Check which Git account is currently set as global
CURRENT_USER=$(git config --global user.name)

# Define an array of options
options=("$USER_1" "$USER_2" "Don't Switch")
num_options=${#options[@]}

# Initialize the selected option
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
    if [ $selected -eq 0 ] && [ "$CURRENT_USER" != "$USER_1" ]; then
      git config --global user.name "$USER_1"
      git config --global user.email "$EMAIL_1"
      echo "Switched to $USER_1 Git account"
      break
    elif [ $selected -eq 1 ] && [ "$CURRENT_USER" != "$USER_2" ]; then
      git config --global user.name "$USER_2"
      git config --global user.email "$EMAIL_2"
      echo "Switched to $USER_2 Git account"
      break
    elif [ $selected -eq $((num_options - 1)) ]; then
      break
    else
      echo "Already using $CURRENT_USER Git account"
      break
    fi
    ;;
  esac
done