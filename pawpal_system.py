from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Task — a single care activity assigned to a pet
# ---------------------------------------------------------------------------
@dataclass
class Task:
    title: str
    description: str
    duration_minutes: int
    priority: str               # "low", "medium", "high"
    task_type: str              # "walk", "feed", "groom", etc.
    frequency: str              # "daily", "weekly", "once"
    completed: bool = False

    def complete(self):
        """Mark this task as done."""
        self.completed = True

    def reset(self):
        """Reset completion status (e.g. start of a new day)."""
        self.completed = False

    def describe(self) -> str:
        """Return a formatted one-line summary of this task and its status."""
        status = "done" if self.completed else "pending"
        return (
            f"[{status}] {self.title} ({self.task_type}, {self.priority} priority) "
            f"— {self.duration_minutes} min, {self.frequency}"
        )


# ---------------------------------------------------------------------------
# Pet — stores pet details and its list of care tasks
# ---------------------------------------------------------------------------
@dataclass
class Pet:
    name: str
    species: str
    fur_color: str
    happiness_level: int = 50   # 0–100
    fullness: int = 50          # 0–100
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, title: str):
        """Remove a task by title."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> List[Task]:
        """Return only tasks not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def apply_walk(self):
        """Increase happiness after a walk, clamped to 100."""
        self.happiness_level = min(100, self.happiness_level + 15)

    def apply_feeding(self):
        """Increase fullness after feeding, clamped to 100."""
        self.fullness = min(100, self.fullness + 25)

    def get_status(self) -> str:
        """Return a one-line summary of the pet's current stats and pending task count."""
        pending = len(self.get_pending_tasks())
        return (
            f"{self.name} ({self.species}) | "
            f"Happiness: {self.happiness_level}/100 | "
            f"Fullness: {self.fullness}/100 | "
            f"Pending tasks: {pending}"
        )


# ---------------------------------------------------------------------------
# Owner — manages multiple pets; provides access to all their tasks
# ---------------------------------------------------------------------------
class Owner:
    def __init__(self, name: str, age: int, gender: str, budget: float):
        self.name = name
        self.age = age
        self.gender = gender
        self.budget = budget
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet):
        """Add a pet to the owner's roster."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str):
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Look up a pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> List[tuple]:
        """Return all tasks across every pet as (pet, task) pairs."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def adjust_budget(self, amount: float):
        """Add or subtract from the owner's budget."""
        self.budget += amount


# ---------------------------------------------------------------------------
# Scheduler — the "brain" that retrieves, organizes, and manages tasks
# ---------------------------------------------------------------------------
class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def get_all_pending(self) -> List[tuple]:
        """Retrieve every incomplete task across all pets as (pet, task) pairs."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.completed
        ]

    def build_schedule(self) -> List[tuple]:
        """
        Organize pending tasks by priority (high → medium → low),
        then by duration (shortest first within the same priority).
        Returns a sorted list of (pet, task) pairs.
        """
        priority_order = {"high": 0, "medium": 1, "low": 2}
        pending = self.get_all_pending()
        return sorted(
            pending,
            key=lambda pt: (priority_order.get(pt[1].priority, 99), pt[1].duration_minutes)
        )

    def complete_task(self, pet_name: str, task_title: str):
        """Mark a specific task as completed and apply its effect to the pet."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return
        for task in pet.tasks:
            if task.title == task_title:
                task.complete()
                if task.task_type == "walk":
                    pet.apply_walk()
                elif task.task_type == "feed":
                    pet.apply_feeding()
                break

    def reset_daily_tasks(self):
        """Reset all 'daily' tasks across every pet for a new day."""
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.frequency == "daily":
                    task.reset()

    def explain_plan(self) -> str:
        """Return a human-readable summary of today's scheduled tasks."""
        schedule = self.build_schedule()
        if not schedule:
            return "No pending tasks — all done!"
        lines = [f"Schedule for {self.owner.name}'s pets:\n"]
        for pet, task in schedule:
            lines.append(f"  {pet.name}: {task.describe()}")
        return "\n".join(lines)
