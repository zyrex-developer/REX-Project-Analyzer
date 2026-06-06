import sys, json, os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPointF, QLineF
from PyQt5.QtGui import QPen, QBrush, QColor


DB_FILE = "projects.json"


class Cable(QGraphicsLineItem):
    def __init__(self, start_box, end_box):
        super().__init__()
        self.start_box = start_box
        self.end_box = end_box
        self.setPen(QPen(QColor("#00e5ff"), 3))
        self.update_position()

    def update_position(self):
        p1 = self.start_box.sceneBoundingRect().center()
        p2 = self.end_box.sceneBoundingRect().center()
        self.setLine(QLineF(p1, p2))


class Box(QGraphicsRectItem):
    def __init__(self, name, color, x, y, app):
        super().__init__(0, 0, 160, 70)
        self.name = name
        self.color = color
        self.app = app

        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.black, 2))
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable
        )

        self.text = QGraphicsTextItem(name, self)
        self.text.setDefaultTextColor(Qt.white)
        self.text.setPos(15, 22)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.app.update_cables()
        self.app.save_database()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("REX Project Analyzer")
        self.setGeometry(100, 80, 1100, 700)

        self.projects = {}
        self.current_project = None
        self.boxes = []
        self.cables = []
        self.connect_start = None

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        self.project_select = QComboBox()
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("Project name")

        self.box_input = QLineEdit()
        self.box_input.setPlaceholderText("Box name")

        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Color: #3498db")

        self.new_project_btn = QPushButton("New Project")
        self.delete_project_btn = QPushButton("Delete Project")
        self.add_box_btn = QPushButton("Add Box")
        self.connect_btn = QPushButton("Connect Selected Boxes")
        self.delete_box_btn = QPushButton("Delete Selected")
        self.analyze_btn = QPushButton("Analyze")
        self.save_btn = QPushButton("Save")

        self.new_project_btn.clicked.connect(self.new_project)
        self.delete_project_btn.clicked.connect(self.delete_project)
        self.add_box_btn.clicked.connect(self.add_box)
        self.connect_btn.clicked.connect(self.connect_selected_boxes)
        self.delete_box_btn.clicked.connect(self.delete_selected)
        self.analyze_btn.clicked.connect(self.analyze_project)
        self.save_btn.clicked.connect(self.save_database)
        self.project_select.currentTextChanged.connect(self.load_project)

        top = QHBoxLayout()
        top.addWidget(self.project_input)
        top.addWidget(self.new_project_btn)
        top.addWidget(QLabel("Open:"))
        top.addWidget(self.project_select)
        top.addWidget(self.delete_project_btn)

        tools = QHBoxLayout()
        tools.addWidget(self.box_input)
        tools.addWidget(self.color_input)
        tools.addWidget(self.add_box_btn)
        tools.addWidget(self.connect_btn)
        tools.addWidget(self.delete_box_btn)
        tools.addWidget(self.analyze_btn)
        tools.addWidget(self.save_btn)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addLayout(tools)
        layout.addWidget(self.view)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.load_database()

    def new_project(self):
        name = self.project_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Enter project name")
            return

        if name in self.projects:
            QMessageBox.warning(self, "Error", "Project already exists")
            return

        self.projects[name] = {"boxes": [], "cables": []}
        self.project_select.addItem(name)
        self.project_select.setCurrentText(name)
        self.project_input.clear()
        self.save_database()

    def delete_project(self):
        name = self.project_select.currentText()
        if not name:
            return

        confirm = QMessageBox.question(self, "Delete", f"Delete project: {name}?")
        if confirm == QMessageBox.Yes:
            del self.projects[name]
            self.project_select.clear()
            self.scene.clear()
            self.boxes = []
            self.cables = []

            for project in self.projects:
                self.project_select.addItem(project)

            self.save_database()

    def add_box(self):
        if not self.current_project:
            QMessageBox.warning(self, "Error", "Create or select project first")
            return

        name = self.box_input.text().strip()
        color = self.color_input.text().strip() or "#3498db"

        if not name:
            QMessageBox.warning(self, "Error", "Enter box name")
            return

        x = 80 + len(self.boxes) * 30
        y = 80 + len(self.boxes) * 30

        box = Box(name, color, x, y, self)
        self.scene.addItem(box)
        self.boxes.append(box)

        self.box_input.clear()
        self.save_database()

    def connect_selected_boxes(self):
        selected = [item for item in self.scene.selectedItems() if isinstance(item, Box)]

        if len(selected) != 2:
            QMessageBox.warning(self, "Error", "Select exactly 2 boxes")
            return

        cable = Cable(selected[0], selected[1])
        self.scene.addItem(cable)
        self.cables.append(cable)
        cable.setZValue(-1)

        self.save_database()

    def delete_selected(self):
        selected = self.scene.selectedItems()

        for item in selected:
            if isinstance(item, Box):
                self.cables = [
                    c for c in self.cables
                    if c.start_box != item and c.end_box != item
                ]
                self.scene.removeItem(item)
                self.boxes.remove(item)

            elif isinstance(item, Cable):
                self.scene.removeItem(item)
                self.cables.remove(item)

        self.save_database()

    def update_cables(self):
        for cable in self.cables:
            cable.update_position()

    def analyze_project(self):
        names = [box.name.lower() for box in self.boxes]

        result = "Project Analysis\n\n"
        result += f"Total Boxes: {len(self.boxes)}\n"
        result += f"Total Cables: {len(self.cables)}\n\n"

        important = ["frontend", "backend", "database", "security", "api", "deployment"]

        for part in important:
            if part in names:
                result += f"✅ {part} found\n"
            else:
                result += f"⚠️ Missing: {part}\n"

        result += "\nIdeas:\n"
        result += "- Add Authentication box\n"
        result += "- Add Backup box\n"
        result += "- Add Payment box\n"
        result += "- Add AI System box\n"
        result += "- Add Admin Dashboard box\n"

        QMessageBox.information(self, "Analyze Result", result)

    def save_database(self):
        if self.current_project:
            data = {"boxes": [], "cables": []}

            for box in self.boxes:
                data["boxes"].append({
                    "name": box.name,
                    "color": box.color,
                    "x": box.pos().x(),
                    "y": box.pos().y()
                })

            for cable in self.cables:
                data["cables"].append({
                    "from": self.boxes.index(cable.start_box),
                    "to": self.boxes.index(cable.end_box)
                })

            self.projects[self.current_project] = data

        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.projects, f, indent=4)

    def load_database(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.projects = json.load(f)

        self.project_select.clear()

        for project in self.projects:
            self.project_select.addItem(project)

    def load_project(self, project_name):
        if not project_name:
            return

        self.current_project = project_name
        self.scene.clear()
        self.boxes = []
        self.cables = []

        data = self.projects.get(project_name, {"boxes": [], "cables": []})

        for item in data["boxes"]:
            box = Box(
                item["name"],
                item["color"],
                item["x"],
                item["y"],
                self
            )
            self.scene.addItem(box)
            self.boxes.append(box)

        for item in data["cables"]:
            try:
                cable = Cable(
                    self.boxes[item["from"]],
                    self.boxes[item["to"]]
                )
                cable.setZValue(-1)
                self.scene.addItem(cable)
                self.cables.append(cable)
            except:
                pass


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())