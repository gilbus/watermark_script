#!/usr/bin/env python3

"""
Ein kleines Programm, welches ein PDF-Dokument mit einem anderen signiert.
"""
import sys
import subprocess
import argparse
import shutil
import os
from typing import List

__license__ = 'AGPLv3 or later'
__author__ = 'tluettje'
__version__ = '1.0'

DEFAULT_WATERMARK_PDF = '/vol/fachschaft/share/MBT/watermark_script/fs_watermark.pdf'  # type: str

OUT_FOLDER = '/vol/fachschaft/share/MBT/'

ZENITY_PATH = None  # type: str

PDFTK_PATH = None  # type: str

EXPLANATION = """
Dieses Skript nimmt ein oder mehrere digitale Dokumente im PDF-Format entgegen und versieht sie mit dem
Fachschafts-Wasserzeichen (standardmäßig <b>%s</b>) auf allen Seiten.
Das Wasserzeichen kann bei Wunsch frei gewählt werden. Für das Wasserzeichen wird das Programm
`pdftk` benötigt, für den optionalen GUI-Modus `zenity`.
""" % DEFAULT_WATERMARK_PDF

GUI_TEXT = """
Dieser GUI-Modus fragt nur nach den PDF-Dateien und wendet das Standard-Wasserzeichen an, die neuen
Dateien wird unter <b><i>OriginalDateiName</i>_watermark.pdf</b> gespeichert. Auf der Kommandozeile
kann auch ein anderes Wasserzeichen angegeben werden.
"""

ZENITY_NOT_INSTALLED = """
Das Programm <b>zenity</b> ist nicht installiert, wird für den GUI-Modus aber benötigt. Alternativ kann
dieses Skript auch auf der Kommandozeile benutzt werden.
"""

PDFTK_NOT_INSTALLED = """
Das Programm <b>pdftk</b> ist nicht installiert, wird aber benötigt um das Wasserzeichen anzuwenden.
Auf Wiedersehen.
"""

PDFTK_CALL_ERROR = """
Bei dem Aufruf von <b>pdftk</b> ist folgender Fehler aufgetreten:
    <span foreground='red'>{error}</span>

Das ursprüngliche Kommando war:
    <tt>{cmd}</tt>
Bitte melde dich bei %s für weitere Fragen.
Auf Wiedersehen.
""" % __author__

PDFTK_UNKNOWN_ERROR = """
Es ist ein unbekannter Fehler aufgetreten, bitte melde dich bei %s
""" % __author__

SIGN_SUCCESS = """
Es scheint alles funktioniert zu haben. Die signierte Datei wurde unter
    <tt>{path}</tt>
gespeichert.
Einen schönen Tag noch (:
"""

DEFAULT_OUT_FILE = '<OriginalDateiName>_watermark.pdf'

ZENITY_CHOOSE_FILE = """
Bitte wähle in dem nächsten Dialog die zu signierende PDF-Datei aus.
"""

WRONG_FILE = """
Entweder wurde keine Datei ausgewählt oder es ist keine valide PDF-Datei.
Auf Wiedersehen.
"""

def main():
    global PDFTK_PATH, DEFAULT_WATERMARK_PDF
    # make path to watermark absolut
    DEFAULT_WATERMARK_PDF = os.path.abspath(DEFAULT_WATERMARK_PDF)
    parser = argparse.ArgumentParser(description=EXPLANATION,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--file', help='Digitales PDF-Dokument welches signiert werden soll.',
                        type=argparse.FileType('r'))
    parser.add_argument('-w', '--watermark',
                        help='Einseitiges PDF-Dokument, welches als Wasserzeichen verwendet wird',
                        default=DEFAULT_WATERMARK_PDF, type=argparse.FileType('r'))
    parser.add_argument('-o', '--out', help='Name der AusgabeDatei', type=str,
                        default=DEFAULT_OUT_FILE)
    parser.add_argument('--launch-gui', help='Startet den GUI-Modus', action='store_true')

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    PDFTK_PATH = shutil.which('pdftk')
    if args.launch_gui:
        gui(not bool(PDFTK_PATH))
    else:
        # if default out filename make string empty
        if args.out:
            args.out = ""
        do_watermark(args.file.name, os.path.abspath(args.watermark.name), args.out)

def gui(pdftk_missing: bool):
    global ZENITY_PATH
    # we are using zenity as gui
    ZENITY_PATH = shutil.which('zenity')
    # check whether zenity was found
    if not ZENITY_PATH:
        # xmessage should be installed
        xmessage_path = shutil.which('xmessage')
        if not xmessage_path:
            sys.exit(2)
        subprocess.call([xmessage_path, ZENITY_NOT_INSTALLED])
        sys.exit(1)
    if pdftk_missing:
        subprocess.call([ZENITY_PATH, '--error', '--text=%s'%PDFTK_NOT_INSTALLED])
        sys.exit(3)
    # zenity is available
    return_code = subprocess.call([ZENITY_PATH, '--info', '--text=%s' % GUI_TEXT])
    if return_code != 0:
        sys.exit(1)
    return_code = subprocess.call([ZENITY_PATH, '--info', '--text=%s' % ZENITY_CHOOSE_FILE])
    if return_code != 0:
        sys.exit(1)
    try:
        pdf_files = subprocess.check_output(
            [ZENITY_PATH, '--file-selection', '--multiple', '--file-filter=*.pdf']
        ).decode('utf-8').replace('\n', '').split('|')
        print('Received following *.pdf files: {}'.format(pdf_files))
    except subprocess.CalledProcessError:
        subprocess.call([ZENITY_PATH, '--error', '--text=%s' % WRONG_FILE])
        sys.exit(4)
    do_watermark(pdf_files, gui=True)


def do_watermark(pdf_files: List[str], watermark_file: str = DEFAULT_WATERMARK_PDF,
                 out_file: str = "", gui: bool = False):
    for pdf_file in pdf_files:
        pdf_file = os.path.realpath(pdf_file)
        file_wo_ext, ext = os.path.splitext(pdf_file)
        out_file = "%s%s_watermark%s" % (OUT_FOLDER, os.path.basename(file_wo_ext), ext)
        print(pdf_file, file_wo_ext, ext, out_file)
        call_args = [PDFTK_PATH, pdf_file, 'stamp', os.path.abspath(watermark_file),
                     'output', out_file]
        error_msg = ''
        fail = False
        try:
            # pdftk does not use exit codes to signal any error -.-'
            # but in case of success the output is empty, therefore we check for it
            call = subprocess.run(call_args, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            fail = True
            error_msg = PDFTK_UNKNOWN_ERROR
        if call.returncode == 1 or fail:
            error_msg = call.stderr.decode('utf-8') if not fail else error_msg
            if gui:
                subprocess.call(
                    [ZENITY_PATH, '--error', '--text=%s' % PDFTK_CALL_ERROR.format(
                        error=error_msg, cmd=call_args)])
            else:
                print(PDFTK_CALL_ERROR.format(error=error_msg, cmd=call_args), file=sys.stderr)
            sys.exit(6)
        if gui:
            subprocess.call([ZENITY_PATH, '--info', '--text=%s' % SIGN_SUCCESS.format(path=out_file)])
        else:
            print(SIGN_SUCCESS.format(path=out_file))


if __name__=="__main__":
    main()
