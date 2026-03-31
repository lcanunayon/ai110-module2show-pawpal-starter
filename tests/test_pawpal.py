import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


def make_task():
    return Task(
        title="Morning Walk",
        description="Walk around the block",
        duration_minutes=30,
        priority="high",
        task_type="walk",
        frequency="daily",
    )


def test_task_completion_changes_status():
    task = make_task()
    assert task.completed is False
    task.complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", fur_color="golden")
    assert len(pet.tasks) == 0
    pet.add_task(make_task())
    assert len(pet.tasks) == 1
