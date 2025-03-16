"""This module contains the constants used in the tests"""

from enum import Enum


class TaskStatusOptions(str, Enum):
    """Available task status options"""

    TO_DO = "TO_DO"  # "To do"
    IN_PROGRESS = "IN_PROGRESS"  # "In progress"
    COMPLETE = "COMPLETE"  # "Complete"
    ARCHIVE = "ARCHIVE"  # "Archive"
