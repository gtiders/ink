load_conda() {
    # Accept conda executable path as an argument
    local conda_exec_path="$1"
    # Check if argument is provided
    if [ -z "$conda_exec_path" ]; then
        echo "Error: Please provide the path to the conda executable as an argument"
        return 1
    fi
    
    # Check if file exists
    if [ ! -f "$conda_exec_path" ]; then
        echo "Error: Conda executable not found: $conda_exec_path"
        return 1
    fi
    
    # Extract conda installation directory (assuming executable is in {install_dir}/bin/conda)
    local conda_bin_dir=$(dirname "$conda_exec_path")
    local conda_install_dir=$(dirname "$conda_bin_dir")

    # Execute conda initialization hook
    __conda_setup="$("$conda_exec_path" 'shell.zsh' 'hook' 2> /dev/null)"
    if [ $? -eq 0 ]; then
        eval "$__conda_setup"
    else
        # Try initializing through script in profile.d
        local conda_sh_path="$conda_install_dir/etc/profile.d/conda.sh"
        if [ -f "$conda_sh_path" ]; then
            . "$conda_sh_path"
        else
            # Directly add conda binary directory to PATH
            export PATH="$conda_bin_dir:$PATH"
        fi
    fi
    unset __conda_setup
}