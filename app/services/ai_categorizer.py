from typing import List, Optional
import json
from datetime import datetime, timezone
from app.core.exceptions import CacheError
from app.domain.constants.stream_constants import REDIS_STREAM_REPORT_LIGHT_CATEGORIZATION
from app.domain.schema.categorize import CategoryNode, LightCategorizerStreamInformation
from app.adapters.cache.base import CacheInterface, StreamInterface
from app.infra.logger import main_logger
from app.adapters.ai.llm.ollama import OllamaLLMEngine
from app.adapters.cache.utils import encode_redis_stream_payload


class ResQAICategorizer:
    def __init__(self, logger=None, cache: Optional[CacheInterface] = None, stream: Optional[StreamInterface] = None):
        self.logger = logger if logger is not None else main_logger
        self.ollama_engine = OllamaLLMEngine(model="llava") #TODO: change later as a variable.
        self.cache = cache  # Can be None if Redis is not available.
        self.stream = stream

    async def categorize_report(self, title: str, description: str, category_key: str, report_id: Optional[str] = None, correlated_id: Optional[str] = None) -> List[CategoryNode]:
        """
        Recursively categorize a report by drilling down through category hierarchies.

        Args:
            title (str): Report title
            description (str): Report description
            category_key (str): Cache key for categories
            report_id (Optional[str]): Unique report identifier for streaming
            correlated_id (Optional[str]): Correlation ID for request tracking

        Returns:
            List[CategoryNode]: Final leaf categories that match the report
        """
        # Get category tree from cache
        if not self.cache:
            self.logger.log("Redis cache not available. Cannot fetch categories.", "ERROR")
            return []

        categories_json = await self.cache.get(category_key)
        if not categories_json:
            self.logger.log(f"No categories found for key: {category_key}", "WARNING")
            return []

        category_dicts = json.loads(categories_json)
        category_nodes: List[CategoryNode] = [CategoryNode.model_validate(item) for item in category_dicts]

        # Start recursive categorization from top level
        self.logger.debug("\n" + "=" * 60)
        self.logger.debug("Starting Report Categorization")
        self.logger.debug("=" * 60)
        self.logger.debug(f"Title: {title}")
        self.logger.debug(f"Description: {description[:100]}..." if len(description) > 100 else f"Description: {description}")
        self.logger.debug("=" * 60 + "\n")

        final_categories = await self._recursive_categorize(
            title=title,
            description=description,
            categories=category_nodes,
            level=0,
            path=[],
            report_id=report_id,  # propagate report_id for streaming
            correlated_id=correlated_id  # propagate correlated_id for streaming
        )

        self.logger.debug("\n" + "=" * 60)
        self.logger.debug("Final Categorization Results:")
        self.logger.debug("=" * 60)
        for cat in final_categories:
            self.logger.debug(f"  - {cat.name} (ID: {cat.id})")
        self.logger.debug("=" * 60 + "\n")

        # Push a final streaming event once categorization is finished
        if self.stream and report_id:
            stream_payload = LightCategorizerStreamInformation(
                report_id=report_id,
                recognized_categories=[cat.slug for cat in final_categories],
                time_added=datetime.now(timezone.utc).isoformat(),
                is_final=True,
                correlated_id=correlated_id,
            ).model_dump()
            encoded_payload = encode_redis_stream_payload(stream_payload)
            self.logger.debug(
                f"[STREAM] Pushing FINAL stream payload for report_id={report_id}: "
                f"{[cat.slug for cat in final_categories]}"
            )
            await self.stream.add_to_stream(REDIS_STREAM_REPORT_LIGHT_CATEGORIZATION, encoded_payload)

        return final_categories

    async def _recursive_categorize(
        self,
        title: str,
        description: str,
        categories: List[CategoryNode],
        level: int,
        path: List[str],
        report_id: Optional[str] = None,
        correlated_id: Optional[str] = None
    ) -> List[CategoryNode]:
        """
        Recursively categorize through the category tree.

        Args:
            title (str): Report title
            description (str): Report description
            categories (List[CategoryNode]): Current level categories to check
            level (int): Current recursion depth
            path (List[str]): Current category path for display
            report_id (Optional[str]): Unique report identifier for streaming
            correlated_id (Optional[str]): Correlation ID for request tracking

        Returns:
            List[CategoryNode]: Leaf categories that match
        """
        if not categories:
            return []

        indent = "  " * level
        self.logger.debug(f"{indent}🔍 Level {level}: Analyzing {len(categories)} categories")
        self.logger.debug(f"{indent}Current path: {' > '.join(path) if path else 'Root'}")

        # Get AI categorization for current level
        category_ids = await self.ollama_engine.categorize_report(
            title=title,
            description=description,
            categories=categories
        )

        if not category_ids:
            self.logger.debug(f"{indent}❌ No matching categories at this level")
            return []

        # Find the actual category nodes that match
        matched_categories = [cat for cat in categories if cat.id in category_ids]

        # Stream intermediate result after every categorization step if stream is available and report_id is provided
        if self.stream and report_id:
            try:
                stream_payload = LightCategorizerStreamInformation(
                    report_id=report_id,
                    recognized_categories=[cat.slug for cat in matched_categories],
                    time_added=datetime.now(timezone.utc).isoformat(),
                    is_final=False,
                    correlated_id=correlated_id,
                ).model_dump()

                encoded_payload = encode_redis_stream_payload(stream_payload)

                self.logger.debug(
                    f"{indent}[STREAM] Pushing intermediate stream payload for report_id={report_id}: "
                    f"{[cat.slug for cat in matched_categories]}"
                )
                await self.stream.add_to_stream(REDIS_STREAM_REPORT_LIGHT_CATEGORIZATION, encoded_payload)
            except CacheError as e:
                self.logger.debug(f"{indent}Stream push failed: {str(e)}")

        self.logger.debug(f"{indent}✅ Found {len(matched_categories)} matching categories:")
        for cat in matched_categories:
            self.logger.debug(f"{indent}   - {cat.name} (ID: {cat.id})")

        # For each matched category, recursively check subcategories
        final_results = []

        for matched_cat in matched_categories:
            new_path = path + [matched_cat.name]

            # If this category has children, recurse deeper
            if matched_cat.children and len(matched_cat.children) > 0:
                self.logger.debug(f"\n{indent}🔽 Drilling into '{matched_cat.name}' subcategories...")
                sub_results = await self._recursive_categorize(
                    title=title,
                    description=description,
                    categories=matched_cat.children,
                    level=level + 1,
                    path=new_path,
                    report_id=report_id,
                    correlated_id=correlated_id,
                )

                # If we found specific subcategories, use those
                if sub_results:
                    final_results.extend(sub_results)
                else:
                    # No subcategories matched, use the parent category
                    self.logger.debug(f"{indent}⚠️  No subcategories matched, using parent: {matched_cat.name}")
                    final_results.append(matched_cat)
            else:
                # Leaf category (no children), this is a final result
                self.logger.debug(f"{indent}🎯 Leaf category reached: {matched_cat.name}")
                final_results.append(matched_cat)

        return final_results
