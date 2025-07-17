import os
import json
import logging
from dotenv import load_dotenv

from src.notion.fetch import NotionBlockExtractor

load_dotenv()
ENV = os.getenv("ENV", "local")

logging_handlers = [logging.StreamHandler()] + ([logging.FileHandler('app.log')] if ENV=="local" else [])

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=logging_handlers
)

logger = logging.getLogger(__name__)
logger.info("Application started")

def main():
    notion_block_extractor = NotionBlockExtractor()
    page_id = input("Provide page id: ")
    flat_blocks, all_pages = notion_block_extractor.gather_nested_page_blocks(page_id)

    with open("data/raw/flat_blocks.json", "w", encoding="utf-8") as f:
        json.dump(flat_blocks, f, ensure_ascii=False, indent=4)

    with open("data/raw/all_pages.json", "w", encoding="utf-8") as f:
        json.dump(all_pages, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
