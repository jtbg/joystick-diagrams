from os import path
from pathlib import Path
import re
import html
import logging
from PyQt5 import QtWidgets
from joystick_diagrams import config
from joystick_diagrams.functions import helper

_logger = logging.getLogger(__name__)


class Export:
    def __init__(self, joystick_listing: dict, parser_id: str = "UNKNOWN"):
        self.export_directory = Path("./diagrams/")
        self.templates_directory = Path("./templates/")
        self.file_name_divider = "_"
        self.joystick_listing = joystick_listing
        self.export_progress = None
        self.no_bind_text = config.noBindText
        self.executor = parser_id
        self.error_bucket = []

    def export_config(self, progress_bar: QtWidgets.QProgressBar = None) -> list:
        """
        Manipulates stored templates, and replaces strings with actual values.

        Returns a list of errors.
        """
        joystick_count = len(self.joystick_listing)

        _logger.debug(f"Export Started with {joystick_count} joysticks")
        _logger.debug(f"Export Data: {self.joystick_listing}")

        if isinstance(progress_bar, QtWidgets.QProgressBar):
            progress_bar.setValue(0)
            progress_increment = int(100 / joystick_count)
            print(progress_increment)

        for joystick in self.joystick_listing:
            base_template = self.get_template(joystick)
            if base_template:
                progress_increment_modes = len(self.joystick_listing[joystick])
                for mode in self.joystick_listing[joystick]:
                    write_template = base_template
                    print("Replacing Strings")
                    completed_template = self.replace_template_strings(joystick, mode, write_template)
                    print("Replacing Unused String")
                    completed_template = self.replace_unused_strings(completed_template)
                    print("Branding")
                    completed_template = self.brand_template(mode, completed_template)
                    print(f"Saving: {joystick}")
                    self.save_template(joystick, mode, completed_template)
                    if isinstance(progress_bar, QtWidgets.QProgressBar):
                        progress_bar.setValue(progress_bar.value() + (progress_increment / progress_increment_modes))
            else:
                self.error_bucket.append(f"No Template file found for: {joystick}")

            if isinstance(progress_bar, QtWidgets.QProgressBar):
                progress_bar.setValue(progress_bar.value() + progress_increment)

        if isinstance(progress_bar, QtWidgets.QProgressBar):
            progress_bar.setValue(100)
        return self.error_bucket

    def get_template(self, joystick: str) -> Optional[str]:
        joystick = joystick.strip()
        template_path = self.templates_directory / f"{joystick}.svg"
        if template_path.exists():
            data = template_path.read_text(encoding="utf-8")
            return data
        return None

    def save_template(self, joystick: str, mode: str, template: str) -> None:
        output_path = self.export_directory / f"{self.executor}_{joystick.strip()}_{mode}.svg"
        helper.create_directory(self.export_directory)
        try:
            with open(output_path, "w", encoding="UTF-8") as outputfile:
                outputfile.write(template)
        except PermissionError as e:
            _logger.error(e)
            raise

    def replace_unused_strings(self, template):
        regex_search = "\\bButton_\\d+\\b|\\bPOV_\\d+_\\w+\\b"
        matches = re.findall(regex_search, template, flags=re.IGNORECASE)
        matches = list(dict.fromkeys(matches))
        if matches:
            for i in matches:
                search = "\\b" + i + "\\b"
                template = re.sub(
                    search,
                    html.escape(self.no_bind_text),
                    template,
                    flags=re.IGNORECASE,
                )
        return template

    def replace_template_strings(self, device, mode, template):
        for button, value in self.joystick_listing[device][mode]["Buttons"].items():
            if value == "NO BIND":
                value = self.no_bind_text
            regex_search = "\\b" + button + "\\b"
            template = re.sub(regex_search, html.escape(value), template, flags=re.IGNORECASE)
        return template

    def brand_template(self, title, template):
        template = re.sub("\\bTEMPLATE_NAME\\b", title, template)
        return template
