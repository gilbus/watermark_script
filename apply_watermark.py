#!/usr/bin/env python3
"""
Dieses Skript nimmt ein oder mehrere digitale Dokumente im PDF-Format entgegen und
versieht sie mit dem Fachschafts-Wasserzeichen auf allen Seiten.

Das Wasserzeichen kann bei Wunsch frei gewählt werden. Für das Wasserzeichen wird das
Programm `pdftk` benötigt, für den optionalen GUI-Modus `zenity`. Die wichtigsten
Optionen können in der Kommandozeilen-Version oder mithilfe einer Konfigurationsdatei
namens `config.toml` im gleichen Ordner wie dieses Skript geändert werden.
"""
from pathlib import Path
from subprocess import run, STDOUT, PIPE as CAPTURE, CalledProcessError
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from sys import stderr
from string import Template
from shutil import which
from collections import ChainMap

try:
    import toml
except ImportError:
    print("This script requires python(3?)-toml, please install it")
    exit(1)

# sorry for the language mess, it once started in german and i automatically extended it
# in english...

__license__ = "AGPLv3 or later"
__author__ = "tluettje"
__version__ = "1.0"
__url__ = "github.com/gilbus/watermark_script"
# {{{ messages
ZENITY_NOT_INSTALLED = """
Das Programm `zenity` ist nicht installiert, wird für den GUI-Modus aber benötigt.
Alternativ kann dieses Skript auch auf der Kommandozeile benutzt werden.
"""

# HTML like markup is rendered inside zenity
PDFTK_NOT_INSTALLED = """
Das Programm <b>pdftk</b> ist nicht installiert, wird aber benötigt um das Wasserzeichen
anzuwenden.
Auf Wiedersehen.
"""

WATERMARK_FILE_ERROR = """
Beim Öffnen der Datei mit dem Wasserzeichen ist ein Fehler aufgetreten:
    <span foreground='red'>{error}</span>
"""

PDF_INPUT_ERROR = """
Beim Öffnen der PDF-Datei ist ein Fehler aufgetreten:
    <span foreground='red'>{error}</span>
"""

PDFTK_CALL_ERROR = """
Bei dem Aufruf von <b>pdftk</b> ist folgender Fehler aufgetreten:
    <span foreground='red'>{{error}}</span>

Das ursprüngliche Kommando war:
    <tt>{{cmd}}</tt>
Bitte melde dich bei {author} bei weiteren Fragen oder öffne ein Issue auf Github
({url}).
Auf Wiedersehen.
""".format(
    author=__author__, url=__url__
)

PDFTK_UNKNOWN_ERROR = """Es ist ein unbekannter Fehler aufgetreten:
<span foreground='red'>{{error}}</span>"""

FILE_SAVE_ERROR = """
Konnte die produzierte PDF-Datei nicht unter <tt>{path}</tt> speichern. Der Fehler war:
    <span foreground='red'>{error}</span>
"""

SIGN_SUCCESS = """
Es scheint alles funktioniert zu haben. Die signierte Datei wurde unter
    <tt>{path}</tt>
gespeichert.
Einen schönen Tag noch (:
"""

OUTPUT_TEMPLATE_ERROR = """
Beim Einsetzen der Werte in das Template (`{template.template}`) für den Namen der
Ausgabedatei ist ein Fehler aufgetreten:
<span foreground='red'>{error}</span>
"""

# }}}
default_config = {
    "output_folder": Path(Path(__file__).parent / "out").absolute(),
    "watermark_pdf": Path(
        Path(__file__).parent / "resources" / "fs_watermark.pdf"
    ).absolute(),
    "zenity_path": which("zenity"),
    "pdftk_path": which("pdftk"),
    "output_template": "${stem}_watermark${suffix}",
}

local_config_file = Path(__file__).parent / "config.toml"


def load_config() -> ChainMap:
    """
    Loads a local config file and returns a ChainMap where local config entries shadow
    their defaults.
    """
    config = ChainMap(default_config)
    try:
        local_config = toml.loads(local_config_file.read_text())
        # ignore empty local config
        if local_config:
            print("Using local config from: ", local_config_file, file=stderr)
            return config.new_child(local_config)
        else:
            print("Ignoring empty local config from: ", local_config_file, file=stderr)
    except FileNotFoundError:
        print(
            "No local config file at `{}` detected, using global one".format(
                local_config_file
            ),
            file=stderr,
        )
    except PermissionError:
        print(
            "Local config file `{}` found but could not read it. Skipping".format(
                local_config_file
            ),
            file=stderr,
        )
    except BaseException as e:
        print("Unexpected error: `{}`. Aborting".format(e), file=stderr)
        exit(1)
    return config


def main() -> int:
    config = load_config()
    parser = ArgumentParser(
        description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "file",
        help="Digitale PDF-Dokumente welche signiert werden sollen.",
        nargs="*",
        type=Path,
    )
    parser.add_argument(
        "-w",
        "--watermark",
        help="Einseitiges PDF-Dokument, welches als Wasserzeichen verwendet wird",
        default=config["watermark_pdf"],
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        help="Name des Ausgabe-Ordners",
        type=Path,
        default=config["output_folder"],
    )
    parser.add_argument(
        "-t",
        "--output-template",
        type=Template,
        help="""Template string to construct the name of the output file. The values
            are taken from the input filename. Don't forget to use single-ticks to
            prevent your shell from expanding the arguments. $stem: Filename without
            suffix. $suffix:
            Rightmost extension with leading dot.""",
        default=config["output_template"],
    )
    parser.add_argument(
        "-g", "--gui", help="Startet den GUI-Modus", action="store_true"
    )
    parser.add_argument(
        "-d",
        "--dump-default-config",
        help="Print the default config in TOML format, useful to create a local config.",
        action="store_true",
    )

    args = parser.parse_args()

    if args.dump_default_config:
        print(toml.dumps({key: str(value) for key, value in default_config.items()}))
        return 0
    if args.gui:
        if not config["zenity_path"]:
            print(ZENITY_NOT_INSTALLED)
            return 1
        try:
            run(
                [config["zenity_path"], "--info", "--text={}".format(__doc__)],
                check=True,
            )
        except CalledProcessError:
            # user closed window instead of clicking OK
            return 0
    elif not args.file:
        parser.print_help()
        return 0

    def show_error_msg(msg: str) -> None:
        """
        If GUI mode is active show the error via zenity and print it always.
        """
        print(msg)
        if args.gui:
            run([config["zenity_path"], "--error", "--text={}".format(msg)])
        exit(1)

    if not config["pdftk_path"]:
        if args.gui:
            run(
                [
                    config["zenity_path"],
                    "--error",
                    "--text={}".format(PDFTK_NOT_INSTALLED),
                ]
            )
        else:
            print(PDFTK_NOT_INSTALLED)
            return 1
    try:
        # quick check whether file exists and is readable
        args.watermark.open().close()
    except BaseException as e:
        error_msg = WATERMARK_FILE_ERROR.format(error=e)
        show_error_msg(error_msg)
        return 1
    if args.gui:
        try:
            args.file = [
                Path(file)
                for file in run(
                    [
                        config["zenity_path"],
                        "--title='Zu signierende PDF-Dateien auswählen'",
                        "--file-selection",
                        "--multiple",
                        "--file-filter=*.pdf",
                    ],
                    check=True,
                    stdout=CAPTURE,
                    universal_newlines=True,
                )
                .stdout.replace("\n", "")
                .split("|")
            ]
        except CalledProcessError as e:
            print(
                """Either user closed window without selection or an error occurred.
                    Exiting"""
            )
            return 0
    for file in args.file:
        try:
            signed_file = watermark_document(file, args.watermark, config["pdftk_path"])
        except ValueError as e:
            error_msg = PDF_INPUT_ERROR.format(error=e)
            show_error_msg(error_msg)
        except CalledProcessError as e:
            error_msg = PDFTK_UNKNOWN_ERROR.format(error=e, cmd=e.args)
            show_error_msg(error_msg)
        output_template_params = {"stem": file.stem, "suffix": file.suffix}
        try:
            output_filename = Path(
                args.output_folder
                / args.output_template.substitute(output_template_params)
            )
        except (KeyError, ValueError) as e:
            error_msg = OUTPUT_TEMPLATE_ERROR.format(
                error=e, template=args.output_template
            )
            show_error_msg(error_msg)
        try:
            with open(output_filename, "wb") as output_file:
                output_file.write(signed_file)
        except BaseException as e:
            error_msg = FILE_SAVE_ERROR.format(path=output_filename, error=e)
            show_error_msg(error_msg)
            return 1
        success_msg = SIGN_SUCCESS.format(path=output_filename.absolute())
        if args.gui:
            run([config["zenity_path"], "--info", "--text=" + success_msg])
        else:
            print(success_msg)
    return 0


def watermark_document(document: Path, watermark: Path, pdftk: str) -> bytes:
    try:
        # quick check whether file exists and is readable
        document.open().close()
    except BaseException as e:
        raise ValueError(e)

    signed_pdf = run(
        [pdftk, "-", "stamp", str(watermark), "output", "-"],
        stdin=document.open("br"),
        stdout=CAPTURE,
        stderr=CAPTURE,
        check=True,
    )

    return signed_pdf.stdout


if __name__ == "__main__":
    exit(main())
