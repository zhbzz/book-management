from sqlalchemy import desc
from sqlalchemy import or_
from db.model import BookEdge


class PersonalRecommender():
    def __init__(self, book_ids: list):
        # self.idx = 0
        self.books = book_ids
        self.visited = set()

        self.bfs(0)

    def bfs(self, idx: int):
        """
        bfs找评分最高的连接书, 按边权从大到小 yield
        """
        if idx >= len(self.books):
            return
        book_id = self.books[idx]
        if book_id in self.visited:
            return
        self.visited.add(book_id)

        results = BookEdge.query.filter(or_(
                BookEdge.book_id_a == book_id,
                BookEdge.book_id_b == book_id,
            )).order_by(desc(BookEdge.average_weight)).all()

        for result in results:
            if result.book_id_a != book_id:
                res = result.book_id_a
            else:
                res = result.book_id_b

            if res not in self.visited:
                self.books.append(res)

        self.bfs(idx + 1)

    def get_recommended_books(self, n: int) -> list:
        return self.books[0:n]
