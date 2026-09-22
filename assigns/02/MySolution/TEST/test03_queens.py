import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from queens_lambda0 import count_solutions, board_is_safe, make_board


class TestQueensTranslation(unittest.TestCase):
    def test_small_boards(self):
        for n, expected in [(1, 1), (2, 0), (3, 0), (4, 2), (5, 10), (6, 4), (7, 40), (8, 92)]:
            with self.subTest(n=n):
                self.assertEqual(count_solutions(n), expected)

    def test_board_safety(self):
        board = make_board(4, [2, 4, 1, 3])
        self.assertTrue(board_is_safe(board, 0, 2))
        self.assertFalse(board_is_safe(board, 0, 3))
        self.assertFalse(board_is_safe(board, 1, 0))


if __name__ == "__main__":
    unittest.main()
