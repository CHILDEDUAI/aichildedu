"""
Content Service CRUD operations.
"""

from . import categories
from . import tags
from . import content_base
from . import stories
from . import quizzes
from . import lessons
from . import assets
from . import collections
from . import reactions

# Export specific items from each module
from .categories import (
    create_category,
    get_category,
    get_category_by_name,
    get_categories,
    update_category,
    delete_category
)

from .tags import (
    create_tag,
    get_tag,
    get_tag_by_name,
    get_tags,
    update_tag,
    delete_tag
)

from .content_base import (
    get_content,
    get_contents,
    create_content_base,
    update_content_base,
    delete_content
)

from .stories import (
    create_story,
    get_story,
    update_story
)

from .quizzes import (
    create_quiz,
    get_quiz,
    update_quiz
)

from .lessons import (
    create_lesson,
    get_lesson,
    update_lesson
)

from .assets import (
    create_content_asset,
    get_content_asset,
    get_content_assets,
    update_content_asset,
    delete_content_asset
)

from .collections import (
    create_collection,
    get_collection,
    get_collections,
    update_collection,
    delete_collection
)

from .reactions import (
    create_reaction,
    get_content_reactions,
    get_user_reactions,
    delete_reaction
) 