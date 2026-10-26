# Getting started

How to download, open and install HaradaER on each system. This manual only covers what already
works in each version; it is updated as the program is tested in more places. The Portuguese
version is [Primeiros passos](PRIMEIROS-PASSOS.md).

The files are on the repository's **Releases** page, in the latest version. You don't need to
install Python or anything else.

| System | File | Requirements |
|---|---|---|
| [Linux](#linux) | `HaradaER-…-linux.tar.gz` | 64-bit, distributions from 2021 on (Ubuntu 22.04+, Arch, Fedora 35+, Mint 21+) |
| [Windows](#windows) | `HaradaER-…-windows.zip` | Windows 10 or 11, 64-bit |
| [macOS](#macos) | `HaradaER-…-macos.zip` | macOS 14 (Sonoma) or newer, Apple chip (M1 onward) |

---

## Linux

> **Status:** tested in real use (Arch Linux, Wayland).

### Install (recommended)

1. Download `HaradaER-…-linux.tar.gz` and extract it to a folder.
2. Open a terminal in that folder and run, once:

   ```
   ./instalar.sh
   ```

3. Look for **HaradaER** in the applications menu. It shows up with its own icon, and `.xml`
   files get the option **Open with › HaradaER**.

No `sudo` needed: the program goes to `~/.local/bin`, for your user only. After installing, you
can delete the extracted folder. To update, extract the new version and run `./instalar.sh`
again.

**Uninstall:** in the extracted folder, `./instalar.sh --remover`. Preferences are kept in
`~/.config/HaradaER` (delete that folder to reset them).

### Open without installing

In the extracted folder, from the terminal:

```
./HaradaER                  # new model
./HaradaER model.xml        # open a TerraER or HaradaER model
```

Double-clicking the `HaradaER` file usually does **not** work: the file manager opens it with
another program (the browser, for example). Use the terminal or `instalar.sh`.

### If it doesn't open

- **Without Wayland (X11):** install Qt's cursor library: `xcb-util-cursor` on Arch,
  `libxcb-cursor0` on Ubuntu and Debian.
- **"Permission denied":** run `chmod +x HaradaER instalar.sh` in the extracted folder.

---

## Windows

> **Status:** the executable is built and tested automatically for every version; real use on
> Windows is just starting. Let us know if anything odd happens.

### Open

1. Download `HaradaER-…-windows.zip`.
2. Right-click the file › **Extract All…** › **Extract**.
3. Open `HaradaER.exe` in the extracted folder.
4. The first time, Windows shows **"Windows protected your PC"**, because the program has no
   digital signature. Click **More info** (the link below the text) and then **Run anyway**.
   The warning doesn't appear again.

There is no installation: `HaradaER.exe` runs from wherever it is. For a shortcut, right-click it
› **Send to** › **Desktop (create shortcut)** (on Windows 11, **Send to** is under
**Show more options**).

To update, download the new version and replace the old `HaradaER.exe`.

### If it doesn't open

- **"Run anyway" doesn't appear:** right-click `HaradaER.exe` › **Properties**, check
  **Unblock** at the bottom of the General tab › **OK**, and open it again. On school or company
  computers, the machine's policy may block it; in that case, only the administrator can allow it.
- **Slow to open:** the first start takes a few seconds (the program unpacks itself into a
  temporary folder). Wait before clicking again.

---

## macOS

> **Status:** the app is built and tested automatically for every version, but it hasn't been
> opened on a real Mac yet. The steps below are macOS's steps for any unsigned app; let us know
> how it went.

### Install

1. Download `HaradaER-…-macos.zip` and open it (Finder extracts it by itself).
2. Drag **HaradaER.app** to the **Applications** folder.
3. The first time, macOS warns that it can't verify the developer, because the app has no Apple
   signature:
   - right-click (or Control-click) HaradaER › **Open** › **Open**; or
   - if there's no **Open** button (macOS 15 onward), go to **System Settings ›
     Privacy & Security**, scroll to the notice about HaradaER and click **Open Anyway**.

   From then on, it opens normally from Launchpad or the Dock.

To update, drag the new version to Applications and choose **Replace**.

---

## After opening

Use is the same on every system. HaradaER starts in the system's language (Portuguese or
English); to change it, use **View › Language** and open the program again. To get started:

1. Choose **Entity** in the top strip and click the drawing; type the name and press Enter.
2. Create a **Relationship** and another entity the same way.
3. Select the relationship and an entity (Ctrl-click; on a Mac, Cmd-click): the connections that
   fit the pair are highlighted in blue in the strip. Click one of them to link the two.
4. **File › Save** writes an `.xml` that also opens in TerraER 3.14.

Orange outlines and the **Messages** panel point out what the model is missing, such as an entity
without a key attribute. You can turn them off in **View › Structure warnings**.

Found a problem or have an idea? **Help › Report a problem** and **Help › Suggest an
improvement** open the GitHub page already filled in (a GitHub account is needed).

Once a day, when opening, HaradaER checks GitHub for a new version and lets you know; nothing
is downloaded by itself. To turn it off, uncheck **Help › Check when opening**.

All commands are in [Como usar](../README.md#como-usar), in the README (in Portuguese).

---

## Keyboard shortcuts

The same list is in **Help › Keyboard shortcuts** (F1), with search. The one-key shortcuts work
with **Edit › Quick editing** on (Ctrl+Shift+E, or the button on the status bar). With Select
active and one element selected, its family letter changes its type (for example, A on an
attribute makes it a key).

<!-- atalhos: início (gerado por python -m haradaer.gui.shortcuts_dialog) -->

**File**

| Action | Shortcut |
|---|---|
| New | `Ctrl+N` |
| Open | `Ctrl+O` |
| Save | `Ctrl+S` |
| Save as | `Ctrl+Shift+S` |
| Export drawing | `Ctrl+E` |
| Close | `Ctrl+F4` |

**Edit**

| Action | Shortcut |
|---|---|
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |
| Cut | `Ctrl+X` |
| Copy | `Ctrl+C` |
| Paste | `Ctrl+V` |
| Duplicate | `Ctrl+D` |
| Delete | `Del` |
| Select all | `Ctrl+A` |
| Select same kind | `Ctrl+Shift+A` |
| Find | `Ctrl+F` |
| Copy as image | `Ctrl+Shift+C` |
| Quick editing | `Ctrl+Shift+E` |

**Arrange**

| Action | Shortcut |
|---|---|
| Bring to front | `Ctrl+]` |
| Send to back | `Ctrl+[` |
| Group | `Ctrl+G` |
| Ungroup | `Ctrl+Shift+G` |

**View**

| Action | Shortcut |
|---|---|
| Zoom in | `Ctrl++` |
| Zoom out | `Ctrl+-` |
| Actual size | `Ctrl+0` |
| Fit to window | `Ctrl+9` |
| Grid | `Ctrl+'` |

**Help**

| Action | Shortcut |
|---|---|
| Keyboard shortcuts | `F1` |

**Quick editing (Edit › Quick editing)**

| Action | Shortcut |
|---|---|
| Select | `V` |
| Entity → Weak entity → Associative entity | `E` |
| Relationship → Weak relationship | `R` |
| Attribute → Key attribute → Partial key attribute → Multivalued attribute → Derived attribute | `A` |
| Disjunction → Overlap → Union | `G` |
| Participation, side "1" → Total participation, side "1" | `1` |
| Participation, side "N" → Total participation, side "N" | `N` |
| Attribute link | `L` |
| Simple generalization → Optional participation in generalization → Mandatory participation in generalization | `H` |
| Free connection | `C` |
| Go back one step in the cycle | `Shift + letter` |
| Change the selected element's type (with Select) | `Family letter` |
| Create where the mouse is | `Space` |
| Back to Select | `Esc` |

**Mouse and gestures**

| Action | Shortcut |
|---|---|
| Zoom | `Pinch` `or Ctrl + mouse wheel` |
| Scroll the drawing | `Two fingers` `or the mouse wheel` |
| Pan the drawing | `Middle button and drag` |
| Keep the tool after creating | `Shift + click` |
| Edit the name | `Double-click the element` |
| New bend on the connection | `Double-click the line` |
| Remove a bend | `Double-click the bend` |

<!-- atalhos: fim -->
