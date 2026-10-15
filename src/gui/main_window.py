from pathlib import Path

from PySide6.QtCore import (
    QThread, Signal,
    Qt, QSize,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QListWidgetItem
)
from PySide6.QtGui import (
    QIcon,
    QImage,
    QPixmap
)

from PIL import Image

from src.utils import collect_images

from src.library_store import (
    get_index_dir,
        load_library_root,
        save_library_root
)

from src.gui.workers import (IndexWorker, SearchWorker)
from src.indexer import IndexConfig
from src.index_status import check_index_status
from src.image_io import open_image


class MainWindow(QMainWindow):

    search_requested = Signal(str, int)
    search_shutdown_requested = Signal()

    def __init__(self):
        super().__init__()

        self.index_thread: QThread | None = None

        self.index_worker: IndexWorker | None = None

        self.search_thread: QThread | None = None

        self.search_worker: SearchWorker | None = None

        self.search_ready = False

        self._close_requested = False

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

        self.analyze_button = QPushButton(
            "사진 분석 시작"
        )

        self.cancel_button = QPushButton(
            "분석 취소"
        )

        self.progress_bar = QProgressBar()

        self.index_status_label = QLabel(
            "사진 분석을 시작해주세요."
        )

        self.library_status_label = QLabel("")


        # 처음에는 등록 버튼을 사용할 수 없게 한다.
        self.register_button.setEnabled(False)

        self.analyze_button.setEnabled(
            self.library_root is not None
        )

        self.cancel_button.setEnabled(False)

        self.progress_bar.setRange(
            0,
            100
        )

        self.progress_bar.setValue(0)

        self.progress_bar.setFormat(
            "%v / %m (%p%)"
        )

        self.search_input = QLineEdit()
        
        self.search_input.setPlaceholderText(
            "찾고 싶은 사진을 문장으로 검색하세요."
        )


        self.search_button = QPushButton(
            "검색"
        )


        self.search_status_label = QLabel(
            "검색 엔진 준비 전"
        )


        self.search_results_list = QListWidget()

        self.search_results_list.setViewMode(
            QListWidget.IconMode
        )

        self.search_results_list.setIconSize(
            QSize(180, 180)
        )

        self.search_results_list.setGridSize(
            QSize(210, 230)
        )

        self.search_results_list.setResizeMode(
            QListWidget.Adjust
        )

        self.search_results_list.setMovement(
            QListWidget.Static
        )

        self.search_results_list.setSpacing(10)
        

        self.search_input.setEnabled(False)
        self.search_button.setEnabled(False)

        # ------------------------
        # Signal 연결
        # ------------------------

        self.select_folder_button.clicked.connect(
            self.select_folder
        )

        self.register_button.clicked.connect(
            self.register_library
        )

        self.search_button.clicked.connect(
            self.start_search
        )

        self.search_input.returnPressed.connect(
            self.start_search
        )

        self.search_results_list.itemDoubleClicked.connect(
            self.open_search_result
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

        layout.addWidget(self.analyze_button)

        layout.addWidget(self.cancel_button)

        layout.addWidget(self.progress_bar)

        layout.addWidget(self.index_status_label)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.restore_library()

        search_layout = QHBoxLayout()

        search_layout.addWidget(
            self.search_input
        )

        search_layout.addWidget(
            self.search_button
        )

        self.analyze_button.clicked.connect(self.start_indexing)

        self.cancel_button.clicked.connect(self.cancel_indexing)

        layout.addLayout(
            search_layout
        )
        
        layout.addWidget(
            self.search_status_label
        )
        
        layout.addWidget(
            self.search_results_list
        )

    def open_search_result(
        self,
        item: QListWidgetItem,
    ):

        path = item.data(
            Qt.UserRole
        )

        if not path:
            return

        open_image(path)

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
        )
        status = check_index_status(library_root=self.library_root, index_dir=get_index_dir())
        self.index_status_label.setText(status.message)
        if status.valid:
            self.index_status_label.setText(
                f"검색 가능\n"
                f"인덱싱된 사진: "
                f"{status.indexed_count:,}장"
            )
            self.start_search_thread()
        else:
            self.index_status_label.setText(status.message)

        self.analyze_button.setEnabled(True)

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
        )

        self.analyze_button.setEnabled(True)

    def start_indexing(self):

        if self.library_root is None:
            return

        if not self.library_root.exists():
            return

        if (
            self.index_thread is not None
            and self.index_thread.isRunning()
        ):
            return

        cfg = IndexConfig(
            backend="siglip",
            model="google/siglip-base-patch16-224",
            recursive=True,
            batch_size=8,
        )

        self.index_thread = QThread()

        self.index_worker = IndexWorker(
            img_dir=self.library_root,
            out_dir=get_index_dir(),
            cfg=cfg,
        )

        self.index_worker.moveToThread(
            self.index_thread
        )

        self.index_thread.started.connect(
            self.index_worker.run
        )

        self.index_worker.progress.connect(
            self.on_index_progress
        )

        self.index_worker.status.connect(
            self.index_status_label.setText
        )

        self.index_worker.succeeded.connect(
            self.on_index_succeeded
        )

        self.index_worker.cancelled.connect(
            self.on_index_cancelled
        )

        self.index_worker.failed.connect(
            self.on_index_failed
        )

        self.index_worker.finished.connect(
            self.index_thread.quit
        )

        self.index_thread.finished.connect(
            self.index_worker.deleteLater
        )

        self.index_thread.finished.connect(
            self.on_index_thread_finished
        )

        self.set_indexing_state(True)

        self.index_thread.start()

    def set_indexing_state(
        self,
        running: bool
    ):

        self.select_folder_button.setEnabled(
            not running
        )

        self.register_button.setEnabled(
            not running
            and self.selected_folder is not None
        )

        self.analyze_button.setEnabled(
            not running
            and self.library_root is not None
        )

        self.cancel_button.setEnabled(
            running
        )

    def on_index_progress(
        self,
        current: int,
        total: int
    ):

        self.progress_bar.setMaximum(
            total
        )

        self.progress_bar.setValue(
            current
        )

    # 완료
    def on_index_succeeded(self, result):

        self.set_indexing_state(False)
        status = check_index_status(library_root=self.library_root, index_dir=get_index_dir())
        self.index_status_label.setText(
            f"사진 분석 완료\n"
            f"인덱싱: {result.indexed:,}장\n"
            f"건너뜀: {result.skipped:,}장\n"
            f"{status.message}"
        )
        self.start_search_thread()


    # 오류
    def on_index_failed(
        self,
        error: str
    ):

        self.set_indexing_state(False)

        self.index_status_label.setText(
            "사진 분석 중 오류가 발생했습니다."
        )

        print(error)

        QMessageBox.critical(
            self,
            "사진 분석 오류",
            error,
        )

    # 취소
    def cancel_indexing(self):

        if self.index_thread is None:
            return

        if not self.index_thread.isRunning():
            return

        self.index_thread.requestInterruption()

        self.cancel_button.setEnabled(False)

        self.index_status_label.setText(
            "취소 요청 중...\n"
            "현재 처리 중인 사진 배치가 끝나면 중단됩니다."
        )

    # 취소 완료
    def on_index_cancelled(self):

        self.set_indexing_state(False)

        self.index_status_label.setText(
            "사진 분석이 취소되었습니다."
        )

    # thread 객체 정리
    def on_index_thread_finished(self):

        thread = self.index_thread

        self.index_worker = None
        self.index_thread = None

        if thread is not None:
            thread.deleteLater()

        if self._close_requested:
            self._close_requested = False
            self.close()

    def closeEvent(self, event):

        if (
            self.index_thread is not None
            and self.index_thread.isRunning()
        ):

            self._close_requested = True

            self.index_thread.requestInterruption()

            self.index_status_label.setText(
                "사진 분석을 안전하게 종료하는 중.."
            )

            event.ignore()

            return

        event.accept()

    def start_search_thread(self):

        if self.search_thread is not None:
            if self.search_thread.isRunning():
                return

        self.search_ready = False

        self.search_input.setEnabled(False)
        self.search_button.setEnabled(False)

        self.search_status_label.setText(
            "검색 엔진을 불러오는 중..."
        )

        self.search_thread = QThread()

        self.search_worker = SearchWorker(
            index_dir=get_index_dir()
        )

        self.search_worker.moveToThread(
            self.search_thread
        )

        # -----------------------------
        # Thread 시작 → 모델 초기화
        # -----------------------------

        self.search_thread.started.connect(
            self.search_worker.initialize
        )

        # -----------------------------
        # GUI → Worker
        # -----------------------------

        self.search_requested.connect(
            self.search_worker.search
        )

        self.search_shutdown_requested.connect(
            self.search_worker.stop
        )

        # -----------------------------
        # Worker → GUI
        # -----------------------------

        self.search_worker.ready.connect(
            self.on_search_ready
        )

        self.search_worker.status.connect(
            self.search_status_label.setText
        )

        self.search_worker.results_ready.connect(
            self.on_search_results
        )

        self.search_worker.failed.connect(
            self.on_search_failed
        )

        # -----------------------------
        # 종료 처리
        # -----------------------------

        self.search_worker.finished.connect(
            self.search_thread.quit
        )

        self.search_worker.finished.connect(
            self.search_worker.deleteLater
        )

        self.search_thread.finished.connect(
            self.on_search_thread_finished
        )

        self.search_thread.start()

    def on_search_ready(self):

        self.search_ready = True

        self.search_input.setEnabled(True)
        self.search_button.setEnabled(True)

        self.search_status_label.setText(
            "검색 준비 완료"
        )

    def start_search(self):

        if not self.search_ready:
            return

        query = (
            self.search_input
            .text()
            .strip()
        )

        if not query:
            return

        self.search_button.setEnabled(False)

        self.search_status_label.setText(
            f'"{query}" 검색 중...'
        )

        self.search_requested.emit(
            query,
            10,
        )

    def on_search_results(
        self,
        results,
    ):

        self.search_results_list.clear()

        for result in results:

            try:
                pixmap = load_thumbnail(
                    result.path,
                    size=180,
                )

            except Exception as error:

                print(
                    f"[THUMBNAIL ERROR] "
                    f"{result.path}: {error}"
                )

                continue

            item = QListWidgetItem()

            item.setIcon(
                QIcon(pixmap)
            )

            item.setText(
                f"{result.path.name}\n"
                f"{result.similarity:.3f}"
            )

            item.setTextAlignment(
                Qt.AlignHCenter
            )

            item.setData(
                Qt.UserRole,
                str(result.path),
            )

            self.search_results_list.addItem(
                item
            )

        self.search_button.setEnabled(True)

        self.search_status_label.setText(
            f"{len(results)}개의 검색 결과"
        )

    def on_search_failed(
        self,
        error: str
    ):

        self.search_button.setEnabled(
            self.search_ready
        )

        self.search_status_label.setText(
            "검색 중 오류가 발생했습니다."
        )

        print(error)

    def stop_search_thread(self):

        if self.search_thread is None:
            return

        if not self.search_thread.isRunning():
            return

        self.search_ready = False

        self.search_input.setEnabled(False)
        self.search_button.setEnabled(False)

        self.search_shutdown_requested.emit()

    def on_search_thread_finished(self):

        thread = self.search_thread

        self.search_worker = None
        self.search_thread = None

        if thread is not None:
            thread.deleteLater()


def load_thumbnail(
    path: Path,
    size: int = 180,
) -> QPixmap:

    with Image.open(path) as image:

        image = image.convert("RGB")

        image.thumbnail(
            (size, size),
            Image.Resampling.LANCZOS,
        )

        width, height = image.size

        image_bytes = image.tobytes(
            "raw",
            "RGB",
        )

        qimage = QImage(
            image_bytes,
            width,
            height,
            width * 3,
            QImage.Format_RGB888,
        ).copy()

    return QPixmap.fromImage(qimage)