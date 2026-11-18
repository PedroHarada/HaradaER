# Primeros pasos

Cómo descargar, abrir e instalar HaradaER en cada sistema. Este manual solo trata de lo que ya
funciona en cada versión; se actualiza a medida que el programa se prueba en más lugares. La
versión en portugués es [Primeiros passos](PRIMEIROS-PASSOS.md), y la versión en inglés,
[Getting started](GETTING-STARTED.md).

Los archivos están en la página **Releases** del repositorio, en la versión más reciente. No hace
falta instalar Python ni nada más.

| Sistema | Archivo | Requisitos |
|---|---|---|
| [Linux](#linux) | `HaradaER-…-linux.tar.gz` | 64 bits, distribuciones de 2021 en adelante (Ubuntu 22.04+, Arch, Fedora 35+, Mint 21+) |
| [Windows](#windows) | `HaradaER-…-windows.zip` | Windows 10 u 11, 64 bits |
| [macOS](#macos) | `HaradaER-…-macos.zip` | macOS 14 (Sonoma) o posterior, chip Apple (M1 en adelante) |

---

## Linux

> **Situación:** probado en uso real (Arch Linux, Wayland).

### Instalar (recomendado)

1. Descargue el `HaradaER-…-linux.tar.gz` y extráigalo en una carpeta.
2. Abra una terminal en esa carpeta y ejecute, una sola vez:

   ```
   ./instalar.sh
   ```

3. Busque **HaradaER** en el menú de aplicaciones. Aparece con su propio icono, y los archivos
   `.xml` pasan a tener la opción **Abrir con › HaradaER**.

No necesita `sudo`: el programa va a `~/.local/bin`, solo para su usuario. Después de instalar,
puede borrar la carpeta extraída. Para actualizar, use **Actualizar y reiniciar** en el aviso de
versión nueva, o ejecute `HaradaER --atualizar` en la terminal.

**Desinstalar:** en la carpeta extraída, `./instalar.sh --remover`. Las preferencias quedan en
`~/.config/HaradaER` (borre esa carpeta si quiere ponerlas a cero).

### Abrir sin instalar

En la carpeta extraída, desde la terminal:

```
./HaradaER                  # modelo nuevo
./HaradaER modelo.xml       # abrir un modelo de TerraER o de HaradaER
```

El doble clic en el archivo `HaradaER` suele **no** funcionar: el gestor de archivos lo abre con
otro programa (el navegador, por ejemplo). Use la terminal o el `instalar.sh`.

### Si no abre

- **Sin Wayland (X11):** instale la biblioteca del cursor de Qt: `xcb-util-cursor` en Arch,
  `libxcb-cursor0` en Ubuntu y en Debian.
- **"Permiso denegado":** ejecute `chmod +x HaradaER instalar.sh` en la carpeta extraída.

---

## Windows

> **Situación:** el ejecutable se genera y se prueba automáticamente en cada versión; el uso real
> en Windows está empezando. Avise si pasa algo raro.

### Abrir

1. Descargue el `HaradaER-…-windows.zip`.
2. Haga clic con el botón derecho en el archivo › **Extraer todo…** › **Extraer**.
3. Abra el `HaradaER.exe` de la carpeta extraída.
4. La primera vez, Windows muestra **"Windows protegió su PC"**, porque el programa no tiene
   firma digital. Haga clic en **Más información** (el enlace debajo del texto) y después en
   **Ejecutar de todas formas**. Las siguientes veces el aviso no aparece.

No hay instalación: el `HaradaER.exe` funciona desde donde esté. Para tener un acceso directo,
haga clic con el botón derecho en él › **Enviar a** › **Escritorio (crear acceso directo)** (en
Windows 11, **Enviar a** está en **Mostrar más opciones**).

Para actualizar, use **Actualizar y reiniciar** en el aviso de versión nueva. Si no se puede
escribir en la carpeta del programa, descargue la versión nueva y reemplace el `HaradaER.exe`
antiguo.

### Si no abre

- **No aparece "Ejecutar de todas formas":** haga clic con el botón derecho en el
  `HaradaER.exe` › **Propiedades**, marque **Desbloquear** abajo, en la pestaña General, ›
  **Aceptar**, y ábralo de nuevo. En equipos de escuela o de empresa, la política del equipo
  puede impedirlo; en ese caso, solo el administrador puede permitirlo.
- **Tarda en abrir:** el primer inicio lleva unos segundos (el programa se descomprime en una
  carpeta temporal). Espere antes de hacer clic otra vez.

---

## macOS

> **Situación:** la aplicación se genera y se prueba automáticamente en cada versión, pero todavía
> no se ha abierto en un Mac de verdad. Los pasos de abajo son los de macOS para cualquier
> aplicación sin firma; cuéntenos cómo le fue.

### Instalar

1. Descargue el `HaradaER-…-macos.zip` y ábralo (el Finder lo extrae solo).
2. Arrastre **HaradaER.app** a la carpeta **Aplicaciones**.
3. La primera vez, macOS avisa que no puede verificar al desarrollador, porque la aplicación no
   tiene firma de Apple:
   - haga clic con el botón derecho (o Control + clic) en HaradaER › **Abrir** › **Abrir**; o
   - si no aparece el botón **Abrir** (macOS 15 en adelante), vaya a **Ajustes del Sistema ›
     Privacidad y seguridad**, baje hasta el aviso sobre HaradaER y haga clic en
     **Abrir igualmente**.

   Las siguientes veces se abre normalmente desde el Launchpad o el Dock.

Para actualizar, use **Actualizar y reiniciar** en el aviso de versión nueva (con HaradaER en
Aplicaciones). También puede arrastrar la versión nueva a Aplicaciones y elegir **Reemplazar**.

---

## Después de abrir

El uso es el mismo en cualquier sistema. HaradaER se abre en el idioma del sistema (portugués,
inglés o español); para cambiarlo, use **Ver › Idioma** y abra el programa de nuevo. Para
empezar:

1. Elija **Entidad** en la franja de arriba y haga clic en el dibujo; escriba el nombre y pulse
   Enter.
2. Cree una **Relación** y otra entidad de la misma forma.
3. Seleccione la relación y una entidad (Ctrl + clic; en Mac, Cmd + clic): las conexiones que
   sirven para el par se resaltan en azul en la franja. Haga clic en una de ellas para unir los
   dos.
4. **Archivo › Guardar** escribe un `.xml` que también se abre en TerraER 3.14.

Los contornos naranjas y el panel **Mensajes** señalan lo que falta en el modelo, como una
entidad sin atributo clave. Puede desactivarlos en **Ver › Avisos de estructura**.

HaradaER no usa la conexión libre de TerraER, que no tiene significado en el modelo. Si un
archivo tiene alguna, se borra al abrirlo, con un aviso que dice entre qué elementos estaba; el
archivo solo cambia cuando usted lo guarde.

Para escribir una nota en el dibujo, use **Texto** (al final de la franja, o la tecla `T` en la
Edición rápida): haga clic para una caja estándar, o arrastre para darle tamaño, y escriba. Enter
corta la línea; hacer clic fuera confirma. La caja crece hacia abajo según el texto, y el ancho
cambia con las asas. Los textos sueltos de TerraER (Texto, Papel) pasan a ser Texto al abrir, con
un aviso; el archivo solo cambia cuando usted lo guarde.

El Texto admite Markdown (CommonMark), y el dibujo lo muestra con formato. En TerraER los
marcadores aparecen tal como se escribieron.

| Escriba | Para obtener |
|---|---|
| `# Título` a `###### Título` | Título, del mayor al menor |
| `*cursiva*` o `_cursiva_` | Cursiva |
| `**negrita**` o `__negrita__` | Negrita |
| `- elemento` o `1. elemento` | Lista; sangre 2 espacios para una sublista |
| `- [ ] tarea` y `- [x] hecha` | Lista de tareas, con casilla; márquela o desmárquela con Ctrl + clic; en Mac, Cmd + clic |
| `[texto](https://sitio)` o `<https://sitio>` | Enlace, que se abre en el navegador (Ctrl + clic; en Mac, Cmd + clic) |
| `` `código` `` o un bloque entre líneas con ```` ``` ```` | Código, en fuente monoespaciada |
| `\*` | Un `*` de verdad (vale para cualquier signo de puntuación) |

Cada Enter es una línea nueva.

¿Encontró un problema o tiene una idea? **Ayuda › Informar de un problema** y **Ayuda › Sugerir
una mejora** abren la página de GitHub ya rellenada (hace falta una cuenta en GitHub).

Una vez al día, al abrir, HaradaER comprueba en GitHub si hay versión nueva y avisa; no se
descarga nada solo. Para desactivarlo, desmarque **Ayuda › Buscar al abrir**.

Todos los comandos están en [Como usar](../README.md#como-usar), en el README (en portugués).

---

## Atajos de teclado

La misma lista está en **Ayuda › Atajos de teclado** (F1), con búsqueda. Los atajos de una tecla
funcionan con **Editar › Edición rápida** activada (Ctrl+Shift+E, o el botón de la barra de
estado). Con Seleccionar activo y un elemento seleccionado, la letra de su familia cambia el tipo
(por ejemplo, A en un atributo lo convierte en clave).

<!-- atalhos: início (gerado por python -m haradaer.gui.shortcuts_dialog) -->

**Archivo**

| Acción | Atajo |
|---|---|
| Nuevo | `Ctrl+N` |
| Abrir | `Ctrl+O` |
| Guardar | `Ctrl+S` |
| Guardar como | `Ctrl+Shift+S` |
| Exportar dibujo | `Ctrl+E` |
| Cerrar | `Ctrl+F4` |

**Editar**

| Acción | Atajo |
|---|---|
| Deshacer | `Ctrl+Z` |
| Rehacer | `Ctrl+Y` |
| Cortar | `Ctrl+X` |
| Copiar | `Ctrl+C` |
| Pegar | `Ctrl+V` |
| Duplicar | `Ctrl+D` |
| Eliminar | `Del` |
| Seleccionar todo | `Ctrl+A` |
| Seleccionar del mismo tipo | `Ctrl+Shift+A` |
| Buscar | `Ctrl+F` |
| Copiar como imagen | `Ctrl+Shift+C` |
| Edición rápida | `Ctrl+Shift+E` |

**Organizar**

| Acción | Atajo |
|---|---|
| Traer al frente | `Ctrl+]` |
| Enviar al fondo | `Ctrl+[` |
| Agrupar | `Ctrl+G` |
| Desagrupar | `Ctrl+Shift+G` |

**Ver**

| Acción | Atajo |
|---|---|
| Acercar | `Ctrl++` |
| Alejar | `Ctrl+-` |
| Tamaño real | `Ctrl+0` |
| Ajustar a la ventana | `Ctrl+9` |
| Cuadrícula | `Ctrl+'` |

**Ayuda**

| Acción | Atajo |
|---|---|
| Atajos de teclado | `F1` |

**Edición rápida (Editar › Edición rápida)**

| Acción | Atajo |
|---|---|
| Seleccionar | `V` |
| Entidad → Entidad débil → Entidad asociativa | `E` |
| Relación → Relación débil | `R` |
| Atributo → Atributo clave → Atributo clave parcial → Atributo multivalor → Atributo derivado | `A` |
| Disyunción → Solapamiento → Unión | `G` |
| Participación, lado "1" → Participación total, lado "1" | `1` |
| Participación, lado "N" → Participación total, lado "N" | `N` |
| Enlace de atributo | `L` |
| Generalización simple → Participación opcional en generalización → Participación obligatoria en generalización | `H` |
| Texto | `T` |
| Retroceder una posición en el ciclo | `Mayús + letra` |
| Cambiar el tipo del elemento seleccionado (con Seleccionar) | `Letra de la familia` |
| Crear donde está el ratón | `Espacio` |
| Volver a Seleccionar | `Esc` |

**Ratón y gestos**

| Acción | Atajo |
|---|---|
| Zoom | `Pellizcar` `o Ctrl + rueda del ratón` |
| Desplazar el dibujo | `Dos dedos` `o la rueda del ratón` |
| Mover el dibujo | `Botón central y arrastrar` |
| Mantener la herramienta después de crear | `Mayús + clic` |
| Editar el nombre | `Doble clic en el elemento` |
| Nuevo vértice en la conexión | `Doble clic en la línea` |
| Quitar un vértice | `Doble clic en el vértice` |

<!-- atalhos: fim -->
