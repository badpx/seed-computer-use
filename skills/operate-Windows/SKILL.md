---
name: operate-Windows
description: This skill enables the Agent to navigate the Windows OS environment (Windows 10/11). It focuses on the "Win-centric" workflow, utilizing the Taskbar, Start Menu, and File Explorer via keyboard-driven logic.
---

## Instructions
### Global System Shortcuts

1. Navigation & Search
| Intent | Shortcut | Notes |
| :--- | :--- | :--- |
| **Open Start / Search** | `Win` or `Win + S` | Best for launching apps. |
| **Run Command** | `Win + R` | Directly launch executables (e.g., `cmd`, `notepad`). |
| **Task View** | `Win + Tab` | Shows all open windows and virtual desktops. |
| **Switch Apps** | `Alt + Tab` | Quick toggle between recent windows. |
| **Task Manager** | `Ctrl + Shift + Esc` | Direct access to kill processes. |
| **Quick Settings** | `Win + A` | Access Wi-Fi, Volume, and Battery. |

2. Window Management (Snap Assist)
| Intent | Shortcut | Action |
| :--- | :--- | :--- |
| **Maximize Window** | `Win + ↑` | Fills the screen. |
| **Minimize Window** | `Win + ↓` | Hides to taskbar. |
| **Snap to Left/Right** | `Win + ← / →` | Splits screen for multitasking. |
| **Minimize All (Desktop)**| `Win + D` | Toggles showing the desktop. |
| **Close Active Window** | `Alt + F4` | Forces app closure. |

---

### File Explorer (Windows Explorer)
| Intent | Shortcut | Action |
| :--- | :--- | :--- |
| **Open File Explorer** | `Win + E` | Launches a new explorer window. |
| **Focus Address Bar** | `Alt + D` or `Ctrl + L` | Allows path typing (e.g., `C:\Users`). |
| **New Folder** | `Ctrl + Shift + N` | Creates folder in current directory. |
| **Delete to Recycle Bin** | `Delete` | Standard delete. |
| **Permanent Delete** | `Shift + Delete` | Bypasses the Recycle Bin. |
| **Rename Item** | `F2` | Quick rename of selected file/folder. |

---

### Agent Execution Strategy

1. **The "Run" Strategy**: For maximum reliability, use `Win + R`, type the app name (e.g., `chrome.exe`), and press `Enter`. This avoids UI search lag.
2. **Path Navigation**: When the Agent needs to find a file, use `Win + E` followed by `Alt + D` to paste the absolute path.
3. **Wait for UI**: Windows animations (especially the Start Menu) take ~200ms. Pause briefly after pressing `Win`.
4. **Context Menus**: Use the `Apps/Menu Key` (or `Shift + F10`) to open right-click menus via keyboard.

## 6. Error Handling
* **UAC Prompts**: If the screen dims and an admin prompt appears, the Agent must be able to send `Alt + Y` (Yes) if it has elevated permissions.
* **Stuck Windows**: If `Alt + F4` fails, use `Ctrl + Shift + Esc` to open Task Manager and terminate the process by name.
