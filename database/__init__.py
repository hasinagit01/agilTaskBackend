from .connection import get_connection, setup_database
from .exceptions import DuplicateError
from .repositories.user_repository import UserRepository
from .repositories.board_repository import BoardRepository
from .repositories.column_repository import ColumnRepository
from .repositories.card_repository import CardRepository
from .repositories.board_member_repository import BoardMemberRepository

user_repository = UserRepository()
board_repository = BoardRepository()
column_repository = ColumnRepository()
card_repository = CardRepository()

__all__ = [
    'get_connection',
    'setup_database',
    'user_repository',
    'UserRepository',
    'board_repository',
    'BoardRepository',
    'column_repository',
    'ColumnRepository',
    'card_repository',
    'CardRepository',
    'DuplicateError',
]