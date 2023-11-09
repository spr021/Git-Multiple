#!/bin/bash

repo_url="https://github.com/spr021/Git-Multiple.git"
script_name="switch.sh"
alias_name="switch"
destination="/Users/local/bin"
git_name=$(git config --global user.name)
git_email=$(git config --global user.email)
# colors
Green='\033[0;32m'
NC='\033[0m'

git clone $repo_url
mv $script_name $destination
chmod +x "$destination/$script_name"
echo "alias $alias_name='$destination/$script_name'" >> ~/.bashrc
source ~/.bashrc

touch "$destination/config.env"
echo "USER_1=\"$git_name\"" > "$destination/config.env"
echo "EMAIL_1=\"$git_email\"" >> "$destination/config.env"

echo -e "${Green}switch installed successfully!${NC}"
