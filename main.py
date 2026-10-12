from pathlib import Path

from src.searcher import SearchEngine


engine = SearchEngine(
    Path("index_test")
)


while True:

    query = input(
        "\n검색어: "
    )

    if query == "exit":
        break

    results = engine.search(
        query=query,
        k=3
    )

    for result in results:

        print(
            result.rank,
            f"{result.similarity:.4f}",
            result.path
        )