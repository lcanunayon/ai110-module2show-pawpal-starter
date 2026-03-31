from dataclasses import dataclass
from typing import List


@dataclass
class Pet:
    name: str
    species: str
    fur_color: str
    happiness_level: int = 50
    fullness: int = 50

    def apply_walk(self):
        pass

    def apply_feeding(self):
        pass

    def get_status(self) -> str:
        pass


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str          # "low", "medium", "high"
    task_type: str         # "walk", "feed", etc.
    target_pet: Pet = None

    def describe(self) -> str:
        pass


class Schedule:
    def __init__(self, date: str, owner: "Owner"):
        self.date = date
        self.owner = owner
        self.tasks: List[CareTask] = []

    def add_task(self, task: CareTask):
        pass

    def remove_task(self, title: str):
        pass

    def explain_plan(self) -> str:
        pass

    def total_duration(self) -> int:
        pass


class Owner:
    def __init__(self, name: str, age: int, gender: str, budget: float):
        self.name = name
        self.age = age
        self.gender = gender
        self.budget = budget
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet):
        pass

    def remove_pet(self, pet_name: str):
        pass

    def generate_schedule(self, date: str, tasks: List[CareTask]) -> Schedule:
        pass

    def adjust_budget(self, amount: float):
        pass
