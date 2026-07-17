import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict

from services.board_cache import BoardCache
from services.board_resolver import BoardResolver
from services.board_creator import BoardCreator

logger = logging.getLogger(__name__)


class BoardManager:
    """
    Board Manager with smart reuse logic.

    - Uses persistent JSON registry to remember created boards across sessions.
    - Avoids Akamai 403 BoardPicker endpoints.
    - Avoids creating duplicate boards with timestamps.
    """

    def __init__(
        self,
        cache: BoardCache,
        resolver: BoardResolver,
        creator: BoardCreator
    ):
        self.cache = cache
        self.resolver = resolver
        self.creator = creator

        # Persistent registry: category_name -> board_id
        self.registry_file = Path(os.getcwd()) / "data" / "boards_registry.json"
        self._created_boards: Dict[str, str] = self._load_registry()
        
        # Default fallback board if create fails (e.g. duplicate error but we don't know the ID)
        self.default_board_id = os.getenv("PINTEREST_BOARD_ID", "972285075743699003")

    def _load_registry(self) -> Dict[str, str]:
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load boards registry: {e}")
        return {}

    def _save_registry(self) -> None:
        try:
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self._created_boards, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save boards registry: {e}")

    def resolve_board(self, product_title: str) -> Optional[str]:
        # 1. Resolve category
        resolution = self.resolver.resolve(product_title)
        category = resolution.board_name

        # 2. Check local persistent registry
        if category in self._created_boards:
            board_id = self._created_boards[category]
            logger.info(f"Reusing existing registry board for '{category}': {board_id}")
            return board_id

        # 3. Try to create board with clean category name
        logger.info(f"Attempting to create board for category: '{category}'")
        create_res = self.creator.create(category)

        if create_res.success and create_res.board_id:
            logger.info(f"Created new board: {create_res.board_name} ({create_res.board_id})")
            self._created_boards[category] = create_res.board_id
            self._save_registry()
            return create_res.board_id

        # 4. Fallback if create failed (likely duplicate but missing ID)
        logger.warning(f"Failed to create '{category}' (likely duplicate). Using fallback board: {self.default_board_id}")
        return self.default_board_id