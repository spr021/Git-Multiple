
# Git Multiple

**Introduction:** MultiGitSwitch is a handy bash script designed for developers who work on a single system but need to manage multiple Git accounts for their projects. Whether you're contributing to personal and work repositories or collaborating on different projects with distinct Git identities, this script simplifies the process of switching between multiple Git configurations seamlessly.

**How to Use:**

1.  Go to this directory on you machine (its diffrent in each OS).
```
/usr/local/bin
```
2.  Clone the repository to your local machine.
```
git clone https://github.com/spr021/Git-Multiple.git
```
3. Go to the directory
```
cd Git-Multiple
```
4. Make the script executable using the `chmod` command:
```
sudo chmod +x switch.sh
```
5. To create an alias for the script, open your shell configuration file (e.g., `~/.bashrc` or `~/.zshrc`) in a text editor. Use the following command for `bash`:
```
alias switch='/usr/local/bin/Git-Multiple/switch.sh'
```
6. Now you can use script every where on your machin and change git account config, just write `switch` on your terminal

**Contributing:** Contributions are welcome! If you encounter any issues, have suggestions, or want to improve the script, feel free to submit a pull request or open an issue.

**License:** This project is licensed under the [MIT License](https://chat.openai.com/c/LICENSE) - see the [LICENSE](https://chat.openai.com/c/LICENSE) file for details.

Simplify your Git workflow with Git Multiple and effortlessly manage multiple Git accounts on a single system. Happy coding!