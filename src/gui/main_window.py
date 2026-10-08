from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.utils import collect_images

from src.library_store import (
    load_library_root,
    save_library_root,
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ------------------------
        # 프로그램 상태
        # ------------------------

        self.selected_folder: Path | None = None
        self.library_root: Path | None = None

        # ------------------------
        # Window 설정
        # ------------------------

        self.setWindowTitle("Local Photo Search")
        self.resize(700, 450)

        # ------------------------
        # UI 요소
        # ------------------------

        self.title_label = QLabel(
            "내 사진 라이브러리"
        )

        self.description_label = QLabel(
            "관리할 사진 폴더를 등록해주세요."
        )

        self.select_folder_button = QPushButton(
            "사진 폴더 선택"
        )

        self.folder_label = QLabel(
            "선택된 폴더 없음"
        )

        self.photo_count_label = QLabel(
            "사진 수: -"
        )

        self.register_button = QPushButton(
            "Library 등록"
        )

        self.library_status_label = QLabel("")

        # 처음에는 등록 버튼을 사용할 수 없게 한다.
        self.register_button.setEnabled(False)

        # ------------------------
        # Signal 연결
        # ------------------------

        self.select_folder_button.clicked.connect(
            self.select_folder
        )

        self.register_button.clicked.connect(
            self.register_library
        )

        # ------------------------
        # Layout
        # ------------------------

        layout = QVBoxLayout()

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)

        layout.addWidget(self.select_folder_button)

        layout.addWidget(self.folder_label)
        layout.addWidget(self.photo_count_label)

        layout.addWidget(self.register_button)

        layout.addWidget(self.library_status_label)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.restore_library()

    def restore_library(self):

        saved_library = load_library_root()

        if saved_library is None:
            return

        self.library_root = saved_library

        if not self.library_root.exists():
            # 없다고 삭제는 하지 않기

            self.library_status_label.setText(
                f"등록된 Library를 찾을 수 없습니다.\n"
                f"경로: {self.library_root}"
            )

            return

        image_paths = collect_images(
            self.library_root,
            recrusive=True
        )

        photo_count = len(image_paths)

        self.library_status_label.setText(
            f"등록된 Library\n"
            f"경로: {self.library_root}\n"
            f"사진: {photo_count:,}장\n"
            f"검색 인덱스: 생성되지 않음"
        )

    def select_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "사진 폴더 선택",
        )

        if not folder:
            return

        self.selected_folder = Path(folder)

        image_paths = collect_images(
            self.selected_folder,
            recrusive=True
        )

        photo_count = len(image_paths)

        self.folder_label.setText(
            f"선택한 폴더: {self.selected_folder}"
        )

        self.photo_count_label.setText(
            f"사진 수: {photo_count:,}장"
        )

        self.register_button.setEnabled(True)

    def register_library(self):

        if self.selected_folder is None:
            return

        self.library_root = self.selected_folder

        save_library_root(self.library_root)

        image_paths = collect_images(
            self.library_root,
            recrusive=True
        )

        photo_count = len(image_paths)

        self.library_status_label.setText(
            f"Library 등록 완료\n"
            f"경로: {self.library_root}\n"
            f"사진: {photo_count:,}장\n"
            f"검색 인덱스: 생성되지 않음"
        )