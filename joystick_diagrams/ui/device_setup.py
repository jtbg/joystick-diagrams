import logging
import sys

import qtawesome as qta
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTreeWidgetItem,
)
from qt_material import apply_stylesheet

from joystick_diagrams.export_device import ExportDevice
from joystick_diagrams.ui.device_setup_controller import (
    get_export_devices,
)
from joystick_diagrams.ui.qt_designer import device_setup_ui

_logger = logging.getLogger(__name__)


class DeviceSetup(QMainWindow, device_setup_ui.Ui_Form):
    devices_updated = Signal()
    device_item_selected = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self.device_header = QTreeWidgetItem()
        self.device_header.setText(0, "Device")
        self.device_header.setText(1, "Profile")
        self.device_header.setText(2, "Status")
        self.treeWidget.setHeaderItem(self.device_header)
        self.treeWidget.setIconSize(QSize(20, 20))

        self.devices_updated.connect(self.initialise_ui)
        self.treeWidget.setColumnCount(3)
        self.treeWidget.itemClicked.connect(self.device_item_clicked)
        self.treeWidget.header().setStretchLastSection(True)
        self.treeWidget.header().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.treeWidget.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.treeWidget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        # Icon Setup
        self.good_icon = qta.icon(
            "fa5s.check-circle",
            color="green",
        )

        self.warning_icon = qta.icon(
            "fa5s.exclamation-triangle",
            color="orange",
        )

        self.bad_icon = qta.icon(
            "fa5s.times-circle",
            color="red",
            color_active="red",
            opacity=0.7,
            scale_factor=1,
        )
        # Init
        self.initialise_ui()

    def initialise_ui(self):
        print("Initialise UI called")
        devices = get_export_devices()

        self.add_devices_to_widget(devices)

    def device_item_clicked(self, data):
        # If root node
        self.device_item_selected.emit(data)

    def view_device_errors(self):
        current_treewidget_row = self.treeWidget.currentItem()
        data = current_treewidget_row.data(0, Qt.UserRole)

        # Format the text, this is horrible

        message_content = f"""
            <h2>Your template {data.template_file_name} is missing {len(data.errors)} controls</h2>
            <strong></strong>
            <p>This won't prevent an export, but you will be missing binds on your final export</p>

            <div class="container" style="inline-size: 100px; overflow-wrap: break-word;">
                <p>
                {data.errors}
                </p>
            </div>

        """

        msgBox = QMessageBox()
        msgBox.setWindowTitle(f"{data.device_name}")
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setText(message_content)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Ok)
        msgBox.exec()

    def add_devices_to_widget(self, export_devices: list[ExportDevice]):
        tree_roots = []
        child_nodes = []
        self.treeWidget.clear()

        identifiers = set([(x.device_id, x.device_name) for x in export_devices])

        def return_top_level_icon_state(
            children_have_template_issues: bool, children_have_errors: bool
        ) -> tuple[QIcon, str]:
            if children_have_template_issues:
                return (self.bad_icon, "A template is not configured")

            if children_have_errors:
                return (self.warning_icon, "One or more profiles have problems")

            return (self.good_icon, "")

        for device_identifier, device_name in identifiers:
            root_item = QTreeWidgetItem()
            # root_item.setStatusTip(0, identifier)
            root_item.setToolTip(0, f"Device GUID: {device_identifier}")
            root_item.setData(0, Qt.UserRole, device_identifier)
            root_item.setText(0, device_name)

            # Get the child items for the root identifier
            child_items = [
                x for x in export_devices if x.device_id == device_identifier
            ]

            root_profile_text = (
                f"{len(child_items)} Profiles"
                if len(child_items) > 1
                else f"{len(child_items)} Profile"
            )

            root_item.setText(1, root_profile_text)
            # Detect if any of the potential children have a missing template, if so all items will be missing template
            children_have_template_issues = bool(
                [x.has_template for x in child_items if not x.has_template]
            )

            # Detect if any of the children have errors, one or more may have errors - Which should trigger a warning
            children_have_errors = bool([x.errors for x in child_items if x.errors])

            root_icon_state, root_message = return_top_level_icon_state(
                children_have_template_issues, children_have_errors
            )

            if not children_have_template_issues:
                for child in child_items:
                    child_item = QTreeWidgetItem()
                    child_item.setData(0, Qt.UserRole, child)
                    child_item.setText(1, child.description)

                    # Get the child icon state where template not exists / or errors bucket contains entries
                    child_icon_state, child_message = return_top_level_icon_state(
                        not child.has_template, bool(child.errors)
                    )

                    child_item.setIcon(2, child_icon_state)

                    child_nodes.append(child_item)

            root_item.addChildren(child_nodes)
            root_item.setIcon(
                2,
                root_icon_state,
            )
            if root_message:
                root_item.setText(2, root_message)

            tree_roots.append(root_item)

        self.treeWidget.addTopLevelItems(tree_roots)
        self.add_view_error_controls_to_tree()
        self.treeWidget.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    def add_view_error_controls_to_tree(self):
        """Adds in widgets to existing treeWidget items. This has to be done post tree setup due to QT"""
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            for c in range(item.childCount()):
                child_item = item.child(c)
                child_data = child_item.data(0, Qt.UserRole)

                if child_data.errors:
                    button = QPushButton("View Errors")
                    button.setProperty("class", "warning")
                    button.setFixedWidth(150)
                    button.setFixedHeight(25)
                    button.setStyleSheet(
                        "padding-left: 5px; padding-right: 3px;"
                        "padding-top: 1px; padding-bottom: 1px;"
                    )
                    button.clicked.connect(self.view_device_errors)
                    self.treeWidget.setItemWidget(child_item, 2, button)


if __name__ == "__main__":
    logger = logging.basicConfig
    app = QApplication(sys.argv)

    window = DeviceSetup()
    window.show()
    apply_stylesheet(app, theme="dark_blue.xml", invert_secondary=False)
    app.exec()