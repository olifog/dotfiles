function cursor --description 'Open a local or SSH path in Cursor'
    # Prefer Cursor's real CLI when it is available, including inside an
    # integrated Cursor terminal on a remote host.
    set -l cursor_cli (type -P cursor 2>/dev/null)
    if test -z "$cursor_cli"; and test (uname) = Darwin
        set cursor_cli /Applications/Cursor.app/Contents/Resources/app/bin/cursor
    end

    if test -n "$cursor_cli"; and test -x "$cursor_cli"
        command "$cursor_cli" $argv
        return $status
    end

    if not set -q SSH_CONNECTION
        echo 'cursor: Cursor CLI not found' >&2
        return 127
    end

    if test (count $argv) -gt 1; or begin; test (count $argv) -eq 1; and string match -qr '^-' -- $argv[1]; end
        echo 'cursor: the SSH shim accepts a single path (default: .)' >&2
        return 2
    end

    set -l remote_path .
    if test (count $argv) -eq 1
        set remote_path $argv[1]
    end

    set remote_path (path resolve -- $remote_path 2>/dev/null)
    if test -z "$remote_path"
        echo 'cursor: path does not exist' >&2
        return 1
    end

    set -l remote_host $DOTFILES_HOST
    if test -z "$remote_host"
        set remote_host $STARSHIP_HOST_ALIAS
    end
    if test -z "$remote_host"
        echo 'cursor: set DOTFILES_HOST to a local SSH config alias for this host' >&2
        return 1
    end

    set -l encoded_path (string escape --style=url -- $remote_path)
    set -l uri "cursor://vscode-remote/ssh-remote+$remote_host$encoded_path"

    printf '\e]8;;%s\e\\Cmd-click to open %s:%s in Cursor\e]8;;\e\\\n' \
        "$uri" "$remote_host" "$remote_path"
end
