import traceback
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
    Slot,
)

from src.indexer import (
    IndexCancelled,
    IndexConfig,
    build_index,
)

from src.searcher import SearchEngine


class IndexWorker(QObject):

    progress = Signal(int, int)

    status = Signal(str)

    succeeded = Signal(object)

    cancelled = Signal()

    failed = Signal(str)

    finished = Signal()


    def __init__(
        self,
        img_dir: Path,
        out_dir: Path,
        cfg: IndexConfig,
    ):
        super().__init__()

        self.img_dir = img_dir
        self.out_dir = out_dir
        self.cfg = cfg


    @Slot()
    def run(self):

        try:
            result = build_index(
                img_dir=self.img_dir,
                out_dir=self.out_dir,
                cfg=self.cfg,

                progress_callback=self.progress.emit,
                status_callback=self.status.emit,

                should_cancel=lambda: (
                    QThread.currentThread()
                    .isInterruptionRequested()
                ),
            )

        except IndexCancelled:

            self.cancelled.emit()

        except Exception:

            self.failed.emit(
                traceback.format_exc()
            )

        else:

            self.succeeded.emit(
                result
            )

        finally:

            self.finished.emit()

class SearchWorker(QObject):

    ready = Signal()

    results_ready = Signal(object)

    failed = Signal(str)

    finished = Signal()

    status = Signal(str)

    def __init__(self, index_dir: Path):
        super().__init__()

        self.index_dir = index_dir
        self.engine: SearchEngine | None = None

    @Slot()
    def initialize(self):

        try:
            self.status.emit(
                "검색 엔진을 불러오는 중..."
            )

            self.engine = SearchEngine(
                self.index_dir
            )

        except Exception:
            self.failed.emit(
                traceback.format_exc()
            )

            self.finished.emit()

            return

        self.status.emit(
            "검색 준비 완료"
        )

        self.ready.emit()

    @Slot(str, int)
    def search(
        self,
        query: str,
        k: int,
    ):

        if self.engine is None:

            self.failed.emit(
                "검색 엔진이 준비되지 않았습니다."
            )

            return

        try:
            results = self.engine.search(
                query=query,
                k=k,
            )

        except Exception:

            self.failed.emit(
                traceback.format_exc()
            )

            return

        self.results_ready.emit(
            results
        )

    @Slot()
    def stop(self):

        self.engine = None

        self.finished.emit()