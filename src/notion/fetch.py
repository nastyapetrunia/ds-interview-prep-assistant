import os
import logging
from collections import deque
from typing import List, Dict, Tuple, Optional

from notion_client import Client

logger = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

class NotionBlockExtractor:
    def __init__(self, api_key: str = NOTION_API_KEY):
        self.client = Client(auth=api_key)

    def gather_nested_page_blocks(self, page_id: str) -> Tuple:
        page = self.client.pages.retrieve(page_id=page_id)
        page_title = self._get_page_title(page)
        page_last_edited = page.get("last_edited_time")

        logger.info(f"Gathering nested data from page: {page_title}")
        return self._walk_blocks_bfs(
            root_page_id=page_id,
            root_page_title=page_title,
            root_page_last_edited=page_last_edited
        )

    def _walk_blocks_bfs(self, root_page_id, root_page_title, root_page_last_edited) -> Tuple:
        pages_queue = deque()
        flat_blocks = []
        all_pages = []

        pages_queue.append({
            "page_id": root_page_id,
            "page_title": root_page_title,
            "parent_page_id": None,
            "parent_page_name": None,
            "page_last_edited": root_page_last_edited,
            "depth": 0
        })

        while pages_queue:
            current_page = pages_queue.popleft()
            all_pages.append(current_page)

            children = self._get_page_children(current_page["page_id"])
            parent_block_id = None

            for child in children:

                block_record = {
                    "parent_page_id": current_page["parent_page_id"],
                    "parent_block_id": parent_block_id,
                    "page_id": current_page["page_id"],
                    "page_title": current_page["page_title"],
                    "depth": current_page["depth"] + 1
                }

                processed_block = self._process_block_data(child)

                if processed_block:
                    block_record.update(processed_block)
                    flat_blocks.append(block_record)

                    if block_record["type"] == "child_page":
                        pages_queue.append({
                                "page_id": block_record["block_id"],
                                "page_title": child['child_page']['title'],
                                "parent_page_id": current_page["page_id"],
                                "parent_page_name": current_page["page_title"],
                                "page_last_edited": block_record["last_edited_time"],
                                "depth": current_page["depth"] + 1
                            }
                        )

                    elif block_record["type"] == "child_database":
                        print("Skipping DB for now...")
                    

                    parent_block_id = block_record["block_id"]

        return flat_blocks, all_pages

    def _get_page_children(self, page_id) -> List:
        children = []
        cursor = None
        while True:
            response = self.client.blocks.children.list(block_id=page_id, start_cursor=cursor)
            children.extend(response["results"])
            cursor = response.get("next_cursor")
            if not cursor:
                break
        return children

    def _process_block_data(self, block) -> Optional[Dict]:
        block_type = block["type"]
        block_id = block["id"]
        content = ""

        if block_type in block and "rich_text" in block[block_type]:
            content = "".join(rt.get("plain_text", "") for rt in block[block_type]["rich_text"])
            if not content:
                return

        elif block_type == "child_page":
            content = f"[Child Page] {block['child_page']['title']}"
        elif block_type == "child_database":
            try:
                db_info = self.client.databases.retrieve(block_id)
                db_title = "".join(t.get("plain_text", "") for t in db_info.get("title", []))
                content = f"[Child Database] {db_title}"
            except Exception as e:
                content = "[Child Database: (Error fetching name)]"
                logger.warning(f"Failed to fetch child database title for id {block_id}: {e}")

        block_data = {
            "block_id": block_id,
            "type": block_type,
            "content": content.strip(),
            "last_edited_time": block.get("last_edited_time", None),
        }

        return block_data

    def _get_page_title(self, page) -> str:
        for val in page.get("properties", {}).values():
            if val.get("type") == "title":
                return "".join(t["plain_text"] for t in val["title"])
        return "[Untitled]"
