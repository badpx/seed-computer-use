---
name: operate-Linux
description: This skill provides the Agent with logic to control Linux distributions (primarily GNOME-based like Ubuntu/Fedora). It prioritizes Terminal-based execution and standard X11/Wayland window management.
---

## Instructions

### Desktop & Window Management

1. GNOME / Standard Desktop
| Intent | Shortcut | Notes |
| :--- | :--- | :--- |
| **Activities Overview** | `Super` | Shows apps and windows. |
| **Open Terminal** | `Ctrl + Alt + T` | Universal shortcut on most distros. |
| **Run Command Menu** | `Alt + F2` | Quick execution of shell commands. |
| **Switch Windows** | `Alt + Tab` | Standard app switcher. |
| **Maximize/Restore** | `Super + ↑ / ↓` | Desktop-level window scaling. |
| **Close Window** | `Ctrl + Q` or `Alt + F4` | Application dependent. |

---

### Terminal Operations (Critical for Linux Agents)
Linux Agents should prefer Terminal over GUI for file and system tasks.

| Intent | Shortcut | Action |
| :--- | :--- | :--- |
| **Copy from Terminal** | `Ctrl + Shift + C` | Standard `Ctrl + C` sends an Interrupt. |
| **Paste to Terminal** | `Ctrl + Shift + V` | Use this instead of `Ctrl + V`. |
| **Interrupt Process** | `Ctrl + C` | Stops the running command. |
| **Suspend Process** | `Ctrl + Z` | Backgrounds the process. |
| **Clear Screen** | `Ctrl + L` | Clears the terminal view. |
| **Reverse Search** | `Ctrl + R` | Searches command history. |

---

### File Management (Nautilus/Thunar)
| Intent | Shortcut | Action |
| :--- | :--- | :--- |
| **Open Location (Path)** | `Ctrl + L` | Turns breadcrumbs into a text path field. |
| **Open Terminal Here** | `Right-Click -> Open in Terminal` | Use context menu logic. |
| **Hidden Files** | `Ctrl + H` | Toggles display of `.` (dot) files. |
| **Properties** | `Alt + Enter` | View file permissions/size. |

---

### Agent Execution Strategy

1. **CLI-First**: Whenever possible, the Agent should use `Ctrl + Alt + T` and perform tasks via Bash/Zsh rather than clicking through folders.
2. **Sudo Handling**: If a command requires `sudo`, the Agent must be prepared to input the password or use `sudo -S` to read from standard input.
3. **Environment Detection**: Before executing, run `echo $XDG_CURRENT_DESKTOP` to determine if the UI is GNOME, KDE, or XFCE, as shortcuts may vary slightly.
4. **The "Alt + F2" Trick**: For launching apps without a terminal, `Alt + F2` then typing the binary name (e.g., `firefox`) is the most direct method.

## 7. Error Handling
* **Frozen UI**: If the GUI hangs, the Agent can try `Ctrl + Alt + F3` to switch to a TTY (TeleType) console to kill the X-server or specific PIDs.
* **Permission Denied**: If a file operation fails in the GUI, the Agent should retry via Terminal using `chmod` or `chown`.
* **Keyboard Layout**: Linux can sometimes default to different layouts; the Agent should verify input via `setxkbmap` if keystrokes appear corrupted.
