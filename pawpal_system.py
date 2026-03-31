import dataclasses
from dataclasses import dataclass, field
from itertools import combinations
from typing import List, Optional
from datetime import date, timedelta


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
    scheduled_time: Optional[str] = None   # "HH:MM" on a 24-h clock, e.g. "08:00"
    due_date: Optional[date] = None        # date this occurrence is due; None = always show
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
        time_str = f" @ {self.scheduled_time}" if self.scheduled_time else ""
        due_str  = f" (due {self.due_date})" if self.due_date else ""
        return (
            f"[{status}] {self.title}{time_str}{due_str} ({self.task_type}, {self.priority} priority) "
            f"— {self.duration_minutes} min, {self.frequency}"
        )

    # ------------------------------------------------------------------
    # Internal helpers used by conflict detection
    # ------------------------------------------------------------------
    def _start_minutes(self) -> Optional[int]:
        """Convert scheduled_time 'HH:MM' to minutes since midnight, or None."""
        if not self.scheduled_time:
            return None
        h, m = self.scheduled_time.split(":")
        return int(h) * 60 + int(m)

    def _end_minutes(self) -> Optional[int]:
        """Return the minute at which this task finishes."""
        start = self._start_minutes()
        if start is None:
            return None
        return start + self.duration_minutes


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

# Priority ranks used in multiple sort operations.
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

# Sentinel value used when a task has no scheduled_time so it sorts last.
_NO_TIME = float("inf")

# Maps each recurring frequency to the timedelta until its next occurrence.
# Adding a new cadence (e.g. "monthly") only requires a new entry here —
# complete_task() needs no changes.
_RECUR_DELTA = {
    "daily":  timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        # Date tracking for smart recurring-task resets.
        self._last_daily_reset: Optional[date] = None
        self._last_weekly_reset: Optional[date] = None

    # ------------------------------------------------------------------
    # 1. FILTERING — get tasks by pet name or completion status
    # ------------------------------------------------------------------

    def get_all_pending(self, today: Optional[date] = None) -> List[tuple]:
        """
        Retrieve every incomplete task that is due on or before today.

        Tasks with no due_date are always included (backwards-compatible with
        tasks created before due_date tracking was added).  Tasks whose
        due_date is in the future are hidden until their day arrives — this is
        what keeps auto-spawned next-occurrences off today's list.
        """
        if today is None:
            today = date.today()
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.completed
            and (task.due_date is None or task.due_date <= today)
        ]

    def get_tasks_for_pet(self, pet_name: str) -> List[tuple]:
        """
        Filter to one pet's tasks.

        Returns (pet, task) pairs for the named pet only (all statuses).
        Returns an empty list if the pet is not found.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return []
        return [(pet, task) for task in pet.tasks]

    def get_tasks_by_status(self, status: str) -> List[tuple]:
        """
        Filter all tasks by completion status.

        status — "pending"   : only incomplete tasks
                 "completed" : only completed tasks
                 "all"       : every task regardless of state
        """
        all_tasks = self.owner.get_all_tasks()
        if status == "pending":
            return [(pet, task) for pet, task in all_tasks if not task.completed]
        if status == "completed":
            return [(pet, task) for pet, task in all_tasks if task.completed]
        return all_tasks   # "all"

    # ------------------------------------------------------------------
    # 2. SORTING — sort tasks by their "HH:MM" scheduled_time string
    # ------------------------------------------------------------------

    def sort_by_time(self, pairs: List[tuple]) -> List[tuple]:
        """
        Sort a list of (pet, task) pairs by scheduled_time in ascending order.

        How the lambda key works
        ------------------------
        sorted() calls the key function once per item and ranks items by the
        returned value.  Here the lambda unpacks each (pet, task) pair, reads
        task.scheduled_time, and returns either the "HH:MM" string or the
        sentinel "99:99".

        "HH:MM" strings sort correctly as plain strings because Python compares
        them character-by-character left-to-right, which is the same order as
        their numeric value (e.g. "07:00" < "18:00" < "23:45").

        Tasks with no scheduled_time receive "99:99" so they always fall to the
        end of the list without causing a TypeError.
        """
        return sorted(
            pairs,
            key=lambda pair: pair[1].scheduled_time if pair[1].scheduled_time else "99:99"
        )

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[tuple]:
        """
        Filter tasks by pet name, completion status, or both at once.

        Parameters
        ----------
        pet_name : str or None
            When provided, keep only tasks belonging to this pet.
        status   : "pending" | "completed" | "all" | None
            When provided, keep only tasks matching this completion state.
            None (default) behaves the same as "all".

        Examples
        --------
        filter_tasks(pet_name="Mochi")                  # all of Mochi's tasks
        filter_tasks(status="pending")                  # every unfinished task
        filter_tasks(pet_name="Luna", status="pending") # Luna's unfinished tasks
        """
        # Start from the full task list, then narrow it down.
        results = self.owner.get_all_tasks()

        if pet_name is not None:
            results = [(p, t) for p, t in results if p.name == pet_name]

        if status == "pending":
            results = [(p, t) for p, t in results if not t.completed]
        elif status == "completed":
            results = [(p, t) for p, t in results if t.completed]
        # status == "all" or None → no further filtering

        return results

    def build_schedule(self, today: Optional[date] = None) -> List[tuple]:
        """
        Sort pending tasks (due today or earlier) by:
          1. scheduled_time (earliest first; unscheduled tasks fall to the end)
          2. priority rank  (high → medium → low)
          3. duration       (shorter tasks first within the same slot)

        Returns a sorted list of (pet, task) pairs.
        """
        pending = self.get_all_pending(today=today)

        def sort_key(pt):
            _, task = pt
            start = task._start_minutes()
            time_rank = start if start is not None else _NO_TIME
            priority_rank = _PRIORITY_RANK.get(task.priority, 99)
            return (time_rank, priority_rank, task.duration_minutes)

        return sorted(pending, key=sort_key)

    # ------------------------------------------------------------------
    # 3. RECURRING TASKS — date-aware reset logic
    # ------------------------------------------------------------------

    def reset_tasks(self, today: Optional[date] = None) -> dict:
        """
        Reset recurring tasks based on the calendar.

        • Daily tasks  — reset once per calendar day.
        • Weekly tasks — reset once per 7-day cycle (tracked from first reset).
        • Once   tasks — never reset; they stay completed forever.

        Returns a summary dict so callers can report what was reset.
        """
        if today is None:
            today = date.today()

        reset_counts = {"daily": 0, "weekly": 0}

        # --- Daily reset ---
        if self._last_daily_reset != today:
            for pet in self.owner.pets:
                for task in pet.tasks:
                    if task.frequency == "daily" and task.completed:
                        task.reset()
                        reset_counts["daily"] += 1
            self._last_daily_reset = today

        # --- Weekly reset ---
        week_elapsed = (
            self._last_weekly_reset is None
            or (today - self._last_weekly_reset) >= timedelta(weeks=1)
        )
        if week_elapsed:
            for pet in self.owner.pets:
                for task in pet.tasks:
                    if task.frequency == "weekly" and task.completed:
                        task.reset()
                        reset_counts["weekly"] += 1
            self._last_weekly_reset = today

        return reset_counts

    # kept for backwards compatibility
    def reset_daily_tasks(self):
        """Legacy wrapper — prefer reset_tasks(today)."""
        self.reset_tasks(date.today())

    # ------------------------------------------------------------------
    # 4. CONFLICT DETECTION — find overlapping time windows
    # ------------------------------------------------------------------

    def detect_conflicts(self, today: Optional[date] = None) -> List[str]:
        """
        Scan today's pending tasks for overlapping time windows and return
        human-readable WARNING strings — never raises an exception.

        Conflict types
        --------------
        SAME-PET  : two tasks assigned to the same pet overlap in time.
                    A pet cannot be walked and groomed simultaneously.
        CROSS-PET : tasks for *different* pets overlap in time.
                    A single owner cannot attend to two animals at once.

        Detection algorithm (lightweight interval overlap check)
        --------------------------------------------------------
        For any two tasks A and B with start times sA, sB and end times
        eA = sA + duration_A, eB = sB + duration_B:

            overlap  <=>  sA < eB  AND  sB < eA

        This is the standard interval-overlap test.  It requires only four
        integer comparisons per pair, so the whole schedule can be scanned
        in O(n^2) without sorting or building any auxiliary structures.

        Tasks without a scheduled_time are skipped — they cannot conflict
        because their time window is unknown.

        Parameters
        ----------
        today : date or None
            Passed to get_all_pending() so only tasks due today are checked.
            Defaults to date.today().

        Returns
        -------
        A list of warning strings (may be empty if no conflicts exist).
        The caller prints or logs these — this method never crashes.
        """
        # Only look at tasks that are both due today and have a clock time.
        pending = self.get_all_pending(today=today)
        timed = [(pet, task) for pet, task in pending if task.scheduled_time]

        warnings: List[str] = []

        # combinations(timed, 2) yields every unique (A, B) pair without index
        # arithmetic — clearer than the equivalent range(len)/range(i+1) loops.
        for (pet_a, task_a), (pet_b, task_b) in combinations(timed, 2):
            start_a = task_a._start_minutes()
            end_a   = task_a._end_minutes()
            start_b = task_b._start_minutes()
            end_b   = task_b._end_minutes()

            # Overlap condition: intervals [sA, eA) and [sB, eB) intersect.
            if start_a < end_b and start_b < end_a:
                kind = "SAME-PET" if pet_a.name == pet_b.name else "CROSS-PET"
                warnings.append(
                    f"WARNING [{kind}] "
                    f"{pet_a.name} '{task_a.title}' "
                    f"({task_a.scheduled_time}, {task_a.duration_minutes} min) "
                    f"overlaps with "
                    f"{pet_b.name} '{task_b.title}' "
                    f"({task_b.scheduled_time}, {task_b.duration_minutes} min)"
                )

        return warnings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def complete_task(
        self, pet_name: str, task_title: str, today: Optional[date] = None
    ) -> Optional["Task"]:
        """
        Mark a task as completed, apply its pet effect, and auto-spawn the
        next occurrence for recurring tasks.

        How timedelta drives the next due date
        ---------------------------------------
        timedelta(days=1)  adds exactly one day to 'today', giving tomorrow's
        date regardless of month boundaries or leap years.

        timedelta(weeks=1) is shorthand for timedelta(days=7) — it always
        produces a date exactly one week later, preserving the day of the week.

        Parameters
        ----------
        today : date or None
            The reference date for calculating the next due date.  Defaults to
            date.today() so production code never needs to pass it.  Tests pass
            a fixed date to keep results deterministic.

        Returns
        -------
        The newly spawned Task if one was created, otherwise None.
        """
        if today is None:
            today = date.today()

        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return None

        spawned: Optional[Task] = None

        for task in pet.tasks:
            if task.title == task_title and not task.completed:
                task.complete()

                # Apply the pet stat effect.
                if task.task_type == "walk":
                    pet.apply_walk()
                elif task.task_type == "feed":
                    pet.apply_feeding()

                # Auto-spawn the next occurrence for recurring frequencies.
                # Dict lookup replaces if/elif: adding "monthly" only needs
                # a new entry in _RECUR_DELTA, not another branch here.
                delta = _RECUR_DELTA.get(task.frequency)
                if delta is not None:
                    spawned = dataclasses.replace(
                        task, completed=False, due_date=today + delta
                    )
                    pet.add_task(spawned)

                # frequency == "once" → delta is None; task stays completed.
                break

        return spawned

    def explain_plan(self, today: Optional[date] = None) -> str:
        """Return a human-readable summary of today's scheduled tasks."""
        schedule = self.build_schedule(today=today)
        if not schedule:
            return "No pending tasks — all done!"
        lines = [f"Schedule for {self.owner.name}'s pets:\n"]
        for pet, task in schedule:
            lines.append(f"  {pet.name}: {task.describe()}")
        return "\n".join(lines)
