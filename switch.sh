#!/bin/bash

source config.env

# Check which Git account is currently set as global
CURRENT_USER=$(git config --global user.name)

echo "Current Git account: $CURRENT_USER"

# Define an array of options
options=($USER_1 $USER_2 "Don't Switch")
num_options=${#options[@]}

# Initialize the selected option
selected=0

Purple='\033[0;35m'
NC='\033[0m' # No Color

# Function to display the menu
display_menu() {
    clear
    for ((i=0; i<num_options; i++)); do
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
            selected=$(( (selected - 1 + num_options) % num_options ))
            display_menu
            ;;
        "B") # Down arrow key
            selected=$(( (selected + 1) % num_options ))
            display_menu
            ;;
        "") # Enter key
            if [ $selected -eq $((num_options - 1)) ]; then
                echo "Goodbye!"
                break
            else
                echo "You chose ${options[selected]}"
                # Add your code for the selected option here
                read -rsn1 -p "Press Enter to continue..."
                display_menu
            fi
            ;;
    esac
done

# # Display a menu to the user
# PS3="Select a Git Account: "
# select choice in "${options[@]}"; do
#   case $REPLY in
#   1)
#     if [[ "$CURRENT_USER" != "$USER_1" ]]; then
#       git config --global user.name "$USER_1"
#       git config --global user.email "$EMAIL_1"
#       echo "Switched to $USER_1 Git account"
#     else
#       echo "Already using $USER_1 Git account"
#     fi
#     ;;
#   2)
#     if [[ "$CURRENT_USER" != "$USER_2" ]]; then
#       git config --global user.name "$USER_2"
#       git config --global user.email "$EMAIL_2"
#       echo "Switched to $USER_2 Git account"
#     else
#       echo "Already using $USER_2 Git account"
#     fi
#     ;;
#   3)
#     echo "Goodbye!"
#     break
#     ;;
#   *)
#     echo "Invalid option"
#     ;;
#   esac
# done
