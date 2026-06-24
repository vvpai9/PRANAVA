from PyQt5.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QLabel,
    QScrollArea,
    QSizePolicy
)

from PyQt5.QtCore import (
    Qt,
    QThread,
    pyqtSignal,
    QTimer
)

from PyQt5.QtGui import QFont

from llm_engine import LLMEngine
from mission_schema import validate_mission
from waypoint_generator import generate_waypoints, save_to_waypoint_file
from mavlink_upload import upload_mission

import random
import time


# =========================================================
# PIPELINE MESSAGE DATABASE
# =========================================================

PIPELINE_MESSAGES = {

    "thinking": [
        "Interpreting your mission request...",
        "Analyzing flight objectives and coordinates...",
        "Building mission structure from operator input...",
        "Preparing autonomous flight plan...",
    ],

    "validation": [
        "Running mission integrity checks...",
        "Verifying coordinates and altitude constraints...",
        "Performing safety validation on generated mission...",
        "Checking waypoint continuity and mission structure...",
    ],

    "validation_success": [
        "Mission validation successful.",
        "All mission parameters look good.",
        "Flight plan cleared for upload.",
        "No structural issues detected in mission profile.",
    ],

    "waypoint_generation": [
        "Generating optimized waypoint trajectory...",
        "Computing survey coverage pattern...",
        "Constructing autonomous navigation path...",
        "Flight path geometry computed successfully...",
    ],

    "uploading": [
        "Establishing MAVLink communication with vehicle...",
        "Uploading mission package to autopilot...",
        "Synchronizing waypoint data with flight controller...",
        "Vehicle link active. Uploading mission items...",
    ],

    "upload_success": [
        "Mission uploaded successfully. Ready for deployment.",
        "Flight controller synchronized successfully.",
        "PRANAVA is standing by for mission execution.",
        "Upload complete. Vehicle ready for autonomous operation.",
    ],

    "upload_failure": [
        "Upload failed. MAVLink communication error detected.",
        "Mission transfer interrupted.",
        "Unable to synchronize mission with vehicle.",
    ]

}


# =========================================================
# BACKGROUND LLM WORKER
# =========================================================

class LLMWorker(QThread):

    finished = pyqtSignal(str, object)
    error = pyqtSignal(str)

    def __init__(self, llm, text):
        super().__init__()
        self.llm = llm
        self.text = text

    def run(self):

        try:
            reply, mission_json = self.llm.chat(self.text)
            self.finished.emit(reply, mission_json)

        except Exception as e:
            self.error.emit(str(e))


# =========================================================
# MISSION WORKER THREAD
# =========================================================

class MissionWorker(QThread):

    progress = pyqtSignal(str)
    success = pyqtSignal()
    failure = pyqtSignal(str)

    def __init__(self, mission_json):

        super().__init__()
        self.mission_json = mission_json

    def emit_stage(self, category, delay=1.2):

        msg = random.choice(PIPELINE_MESSAGES[category])
        self.progress.emit(msg)

        time.sleep(delay)

    def run(self):

        try:

            # =====================================================
            # VALIDATION
            # =====================================================

            self.emit_stage("validation")

            mission = validate_mission(self.mission_json)

            self.progress.emit(
                random.choice(
                    PIPELINE_MESSAGES["validation_success"]
                )
            )

            time.sleep(1)

            # =====================================================
            # MISSION TYPE
            # =====================================================

            mission_name = mission.mission_type.replace("_", " ").title()

            self.progress.emit(
                f"Mission type detected: {mission_name}"
            )

            time.sleep(1)

            # =====================================================
            # WAYPOINT GENERATION
            # =====================================================

            if mission.mission_type == "grid":

                self.progress.emit(
                    "Constructing grid-based survey path..."
                )

            elif mission.mission_type == "spiral_out":

                self.progress.emit(
                    "Generating outward spiral reconnaissance pattern..."
                )

            elif mission.mission_type == "spiral_in":

                self.progress.emit(
                    "Generating inward spiral reconnaissance pattern..."
                )

            else:

                self.emit_stage("waypoint_generation")

            time.sleep(1)

            waypoints = generate_waypoints(mission)

            if not waypoints:

                self.failure.emit("No waypoints were generated.")
                return

            self.progress.emit(
                f"Generated {len(waypoints)} optimized autonomous waypoints."
            )

            time.sleep(1)

            # =====================================================
            # SAVE MISSION FILE
            # =====================================================

            if mission.mission_type in [
                "grid",
                "spiral_in",
                "spiral_out"
            ]:
                global_alt = mission.altitude

            else:
                global_alt = waypoints[0].get("alt", 25.0)

            save_to_waypoint_file(waypoints, global_alt)

            self.progress.emit(
                "Mission waypoints exported successfully."
            )

            time.sleep(1)

            # =====================================================
            # UPLOAD
            # =====================================================

            self.emit_stage("uploading")

            success, reason = upload_mission(
                waypoints,
                global_alt
            )

            if success:

                self.progress.emit(
                    random.choice(
                        PIPELINE_MESSAGES["upload_success"]
                    )
                )

                self.success.emit()

            else:

                self.progress.emit(
                    random.choice(
                        PIPELINE_MESSAGES["upload_failure"]
                    )
                )

                self.progress.emit(
                    f"Upload failed: {reason}\n"
                    "Please verify MAVLink connection and vehicle readiness."
                )

                self.failure.emit(reason)

        except Exception as e:
            self.failure.emit(str(e))


# =========================================================
# CHAT BUBBLE WIDGET
# =========================================================

class ChatBubble(QLabel):

    def __init__(self, text, is_user=False):

        super().__init__(text)

        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.setFont(QFont("Segoe UI", 11))

        self.setContentsMargins(15, 10, 15, 10)

        if is_user:

            self.setStyleSheet("""
                QLabel {
                    background-color: #2b5278;
                    color: white;
                    border-radius: 15px;
                    padding: 10px;
                }
            """)

            self.setAlignment(Qt.AlignRight)

        else:

            self.setStyleSheet("""
                QLabel {
                    background-color: #3a3a3a;
                    color: white;
                    border-radius: 15px;
                    padding: 10px;
                }
            """)

            self.setAlignment(Qt.AlignLeft)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )


# =========================================================
# MAIN UI
# =========================================================

class ChatbotUI(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("PRANAVA - UAV Mission Planner")

        self.setMinimumSize(500, 700)
        self.resize(650, 850)

        self.llm = LLMEngine()

        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.animate_thinking)

        self.thinking_state = 0

        self.thinking_bubble = None

        self.initUI()

    # =====================================================
    # UI SETUP
    # =====================================================

    def initUI(self):

        self.setStyleSheet("""

            QMainWindow {
                background-color: #212121;
            }

            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border-radius: 18px;
                padding: 12px;
                font-size: 14px;
                border: 1px solid #404040;
            }

            QPushButton {
                background-color: #10a37f;
                color: white;
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0e8f6f;
            }

        """)

        central_widget = QWidget()

        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # =====================================================
        # SCROLL AREA
        # =====================================================

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        self.chat_container = QWidget()

        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)

        self.chat_container.setLayout(self.chat_layout)

        self.scroll_area.setWidget(self.chat_container)

        main_layout.addWidget(self.scroll_area)

        # =====================================================
        # INPUT AREA
        # =====================================================

        input_layout = QHBoxLayout()

        self.user_input = QLineEdit()

        self.user_input.setPlaceholderText(
            "Describe your UAV mission..."
        )

        self.user_input.returnPressed.connect(self.send_message)

        input_layout.addWidget(self.user_input)

        self.send_btn = QPushButton("Send")

        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.send_btn)

        main_layout.addLayout(input_layout)

        central_widget.setLayout(main_layout)

        # =====================================================
        # WELCOME MESSAGE
        # =====================================================

        self.add_message(
            "Welcome to PRANAVA.\n"
            "Please specify your UAV mission.",
            is_user=False
        )

    # =====================================================
    # ADD CHAT MESSAGE
    # =====================================================

    def add_message(self, text, is_user=False):

        bubble = ChatBubble(text, is_user)

        wrapper = QWidget()

        wrapper_layout = QHBoxLayout()

        if is_user:

            wrapper_layout.addStretch()
            wrapper_layout.addWidget(bubble, 0)

        else:

            wrapper_layout.addWidget(bubble, 0)
            wrapper_layout.addStretch()

        wrapper.setLayout(wrapper_layout)

        self.chat_layout.addWidget(wrapper)

        # =====================================================
        # AUTO SCROLL
        # =====================================================

        QTimer.singleShot(
            50,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        )

        return bubble

    # =====================================================
    # REMOVE THINKING BUBBLE
    # =====================================================

    def remove_thinking_bubble(self):

        if self.thinking_bubble is not None:

            self.thinking_bubble.hide()
            self.thinking_bubble.deleteLater()

            self.thinking_bubble = None

    # =====================================================
    # SEND MESSAGE
    # =====================================================

    def send_message(self):

        text = self.user_input.text().strip()

        if not text:
            return

        # =====================================================
        # USER MESSAGE
        # =====================================================

        self.add_message(text, is_user=True)

        self.user_input.clear()

        # =====================================================
        # DISABLE INPUT
        # =====================================================

        self.user_input.setEnabled(False)
        self.send_btn.setEnabled(False)

        # =====================================================
        # THINKING BUBBLE
        # =====================================================

        self.thinking_bubble = self.add_message(
            "PRANAVA is analyzing your request.",
            is_user=False
        )

        self.thinking_state = 0

        self.typing_timer.start(500)

        # =====================================================
        # START LLM WORKER
        # =====================================================

        self.worker = LLMWorker(self.llm, text)

        self.worker.finished.connect(self.handle_response)
        self.worker.error.connect(self.handle_error)

        self.worker.start()

    # =====================================================
    # ANIMATE THINKING
    # =====================================================

    def animate_thinking(self):

        states = [
            "PRANAVA is analyzing your request.",
            "PRANAVA is analyzing your request..",
            "PRANAVA is analyzing your request..."
        ]

        if self.thinking_bubble is not None:

            self.thinking_bubble.setText(
                states[self.thinking_state]
            )

        self.thinking_state = (self.thinking_state + 1) % 3

    # =====================================================
    # HANDLE RESPONSE
    # =====================================================

    def handle_response(self, reply, mission_json):

        self.typing_timer.stop()

        self.remove_thinking_bubble()

        self.add_message(reply, is_user=False)

        # =====================================================
        # ENABLE INPUT
        # =====================================================

        self.user_input.setEnabled(True)
        self.send_btn.setEnabled(True)

        self.user_input.setFocus()

        # =====================================================
        # START MISSION PIPELINE
        # =====================================================

        if mission_json is not None:

            thinking_msg = random.choice(
                PIPELINE_MESSAGES["thinking"]
            )

            self.add_message(thinking_msg, is_user=False)

            self.mission_worker = MissionWorker(mission_json)

            self.mission_worker.progress.connect(
                lambda msg: self.add_message(msg, is_user=False)
            )

            self.mission_worker.success.connect(
                lambda: QMessageBox.information(
                    self,
                    "Mission Upload",
                    "Mission uploaded successfully!"
                )
            )

            self.mission_worker.failure.connect(
                lambda err: QMessageBox.warning(
                    self,
                    "Mission Error",
                    err
                )
            )

            self.mission_worker.start()

    # =====================================================
    # HANDLE ERROR
    # =====================================================

    def handle_error(self, error_msg):

        self.typing_timer.stop()

        self.remove_thinking_bubble()

        self.add_message(
            f" Error:\n{error_msg}",
            is_user=False
        )

        self.user_input.setEnabled(True)
        self.send_btn.setEnabled(True)


# =========================================================
# END OF FILE
# =========================================================
