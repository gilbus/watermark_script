# `watermark_script`

Apply a watermark (PDF) on top of one or more PDF files. An optional *graphical* mode is
available with help of *zenity*. This has been developed by and for the student council
of the Faculty of Technology, Bielefeld University to sign copies of old exams.

## Customization

Call `./apply_watermark.py -d > config.toml` and change the config however you like.
Command line arguments always have precedence.

## Usage
```
usage: apply_watermark.py [-h] [-w WATERMARK] [-o OUTPUT_FOLDER]
                          [-t OUTPUT_TEMPLATE] [-g] [-d]
                          [file [file ...]]

Dieses Skript nimmt ein oder mehrere digitale Dokumente im PDF-Format entgegen
und versieht sie mit dem Fachschafts-Wasserzeichen auf allen Seiten. Das
Wasserzeichen kann bei Wunsch frei gewählt werden. Für das Wasserzeichen wird
das Programm `pdftk` benötigt, für den optionalen GUI-Modus `zenity`. Die
wichtigsten Optionen können in der Kommandozeilen-Version oder mithilfe einer
Konfigurationsdatei namens `config.toml` im gleichen Ordner wie dieses Skript
geändert werden.

positional arguments:
  file                  Digitale PDF-Dokumente welche signiert werden sollen.
                        (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -w WATERMARK, --watermark WATERMARK
                        Einseitiges PDF-Dokument, welches als Wasserzeichen
                        verwendet wird (default: /home/tluettje/Coding/waterma
                        rk_script/resources/fs_watermark.pdf)
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Name des Ausgabe-Ordners (default:
                        /home/tluettje/Coding/watermark_script/out)
  -t OUTPUT_TEMPLATE, --output-template OUTPUT_TEMPLATE
                        Template string to construct the name of the output
                        file. The values are taken from the input filename.
                        Don't forget to use single-ticks to prevent your shell
                        from expanding the arguments. $stem: Filename without
                        suffix. $suffix: Rightmost extension with leading dot.
                        (default: ${stem}_watermark${suffix})
  -g, --gui             Startet den GUI-Modus (default: False)
  -d, --dump-default-config
                        Print the default config in TOML format, useful to
                        create a local config. (default: False)

AGPLv3 @ tluettje
```
