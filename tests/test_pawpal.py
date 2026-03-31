import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Helpers — reusable factories so each test starts from a clean state
# ---------------------------------------------------------------------------

def make_task(
    title="Morning Walk",
    description="Walk around the block",
    duration_minutes=30,
    priority="high",
    task_type="walk",
    frequency="daily",
    scheduled_time=None,
    due_date=None,
    completed=False,
):
    return Task(
        title=title,
        description=description,
        duration_minutes=duration_minutes,
        priority=priority,
        task_type=task_type,
        frequency=frequency,
        scheduled_time=scheduled_time,
        due_date=due_date,
        completed=completed,
    )


def make_scheduler():
    """Return a fresh Owner → Pet → Scheduler with no tasks."""
    owner = Owner(name="Alex", age=30, gender="nonbinary", budget=500.0)
    pet = Pet(name="Mochi", species="dog", fur_color="golden")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    return scheduler, owner, pet


TODAY = date(2025, 6, 15)   # fixed so tests are deterministic


# ===========================================================================
# EXISTING TESTS (kept as-is)
# ===========================================================================

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


# ===========================================================================
# TASK — basics
# ===========================================================================

def test_task_reset_clears_completion():
    """complete() followed by reset() should set completed back to False."""
    task = make_task()
    task.complete()
    task.reset()
    assert task.completed is False


def test_task_describe_shows_scheduled_time():
    """describe() should include the HH:MM time when scheduled_time is set."""
    task = make_task(scheduled_time="08:00")
    assert "08:00" in task.describe()


def test_task_describe_shows_due_date():
    """describe() should include the due date when due_date is set."""
    task = make_task(due_date=date(2025, 6, 16))
    assert "2025-06-16" in task.describe()


def test_task_describe_labels_done_vs_pending():
    """describe() should say [done] after completion and [pending] before."""
    task = make_task()
    assert "[pending]" in task.describe()
    task.complete()
    assert "[done]" in task.describe()


# ===========================================================================
# PET — basics
# ===========================================================================

def test_remove_task_by_title():
    """remove_task() should delete only the task with the matching title."""
    pet = Pet(name="Luna", species="cat", fur_color="white")
    pet.add_task(make_task(title="Feed"))
    pet.add_task(make_task(title="Groom"))
    pet.remove_task("Feed")
    titles = [t.title for t in pet.tasks]
    assert "Feed" not in titles
    assert "Groom" in titles


def test_get_pending_tasks_excludes_completed():
    """get_pending_tasks() should only return incomplete tasks."""
    pet = Pet(name="Luna", species="cat", fur_color="white")
    t1 = make_task(title="Walk")
    t2 = make_task(title="Feed")
    t3 = make_task(title="Groom")
    t2.complete()
    pet.add_task(t1)
    pet.add_task(t2)
    pet.add_task(t3)
    pending = pet.get_pending_tasks()
    assert len(pending) == 2
    assert all(not t.completed for t in pending)


def test_apply_walk_increases_happiness():
    """apply_walk() should add 15 to happiness_level, capped at 100."""
    pet = Pet(name="Mochi", species="dog", fur_color="golden", happiness_level=50)
    pet.apply_walk()
    assert pet.happiness_level == 65


def test_apply_walk_clamps_at_100():
    """apply_walk() should not push happiness above 100."""
    pet = Pet(name="Mochi", species="dog", fur_color="golden", happiness_level=95)
    pet.apply_walk()
    assert pet.happiness_level == 100


def test_apply_feeding_increases_fullness():
    """apply_feeding() should add 25 to fullness, capped at 100."""
    pet = Pet(name="Mochi", species="dog", fur_color="golden", fullness=50)
    pet.apply_feeding()
    assert pet.fullness == 75


def test_apply_feeding_clamps_at_100():
    """apply_feeding() should not push fullness above 100."""
    pet = Pet(name="Mochi", species="dog", fur_color="golden", fullness=90)
    pet.apply_feeding()
    assert pet.fullness == 100


# ===========================================================================
# SCHEDULER — SORTING CORRECTNESS
# ===========================================================================

def test_sort_by_time_orders_tasks_chronologically():
    """
    sort_by_time() must return tasks in ascending HH:MM order.

    Why this works: "HH:MM" strings compare correctly as plain strings
    because Python does left-to-right character comparison, which matches
    the numeric time order (e.g. "07:00" < "18:00" < "23:45").
    """
    scheduler, owner, pet = make_scheduler()
    t_afternoon = make_task(title="Afternoon Walk", scheduled_time="14:00")
    t_morning   = make_task(title="Morning Feed",   scheduled_time="08:00")
    t_evening   = make_task(title="Evening Groom",  scheduled_time="23:00")
    pet.add_task(t_afternoon)
    pet.add_task(t_morning)
    pet.add_task(t_evening)

    sorted_pairs = scheduler.sort_by_time(owner.get_all_tasks())
    times = [task.scheduled_time for _, task in sorted_pairs]
    assert times == ["08:00", "14:00", "23:00"]


def test_sort_by_time_puts_unscheduled_tasks_last():
    """
    Tasks without a scheduled_time should fall to the end of the sorted list.

    The sentinel "99:99" is used so None tasks never raise a TypeError
    and always sort after every valid HH:MM string.
    """
    scheduler, owner, pet = make_scheduler()
    t_no_time = make_task(title="No-time Task", scheduled_time=None)
    t_early   = make_task(title="Early Task",   scheduled_time="07:00")
    pet.add_task(t_no_time)
    pet.add_task(t_early)

    sorted_pairs = scheduler.sort_by_time(owner.get_all_tasks())
    last_task = sorted_pairs[-1][1]
    assert last_task.scheduled_time is None


def test_build_schedule_tiebreaks_by_priority_then_duration():
    """
    When two tasks share the same time slot, build_schedule() must put
    high-priority before low-priority.  Within the same priority, the
    shorter task should come first.
    """
    scheduler, _, pet = make_scheduler()
    # Same time, different priorities
    t_low  = make_task(title="Low",  scheduled_time="09:00", priority="low",  duration_minutes=20)
    t_high = make_task(title="High", scheduled_time="09:00", priority="high", duration_minutes=30)
    # Same time AND same priority — different duration
    t_short = make_task(title="Short", scheduled_time="09:00", priority="medium", duration_minutes=10)
    t_long  = make_task(title="Long",  scheduled_time="09:00", priority="medium", duration_minutes=40)
    pet.add_task(t_low)
    pet.add_task(t_high)
    pet.add_task(t_short)
    pet.add_task(t_long)

    schedule = scheduler.build_schedule(today=TODAY)
    titles = [task.title for _, task in schedule]

    assert titles.index("High") < titles.index("Low"),   "high priority must come before low"
    assert titles.index("Short") < titles.index("Long"), "shorter task must come before longer at same priority"


def test_build_schedule_excludes_future_due_dates():
    """
    Tasks whose due_date is tomorrow must NOT appear in today's schedule.
    This is how auto-spawned next-occurrences stay off the current day's list.
    """
    scheduler, _, pet = make_scheduler()
    future_task = make_task(title="Future Walk", due_date=TODAY + timedelta(days=1))
    pet.add_task(future_task)

    schedule = scheduler.build_schedule(today=TODAY)
    assert len(schedule) == 0


def test_build_schedule_includes_task_due_today():
    """A task due exactly today must appear in the schedule."""
    scheduler, _, pet = make_scheduler()
    today_task = make_task(title="Today's Walk", due_date=TODAY)
    pet.add_task(today_task)

    schedule = scheduler.build_schedule(today=TODAY)
    assert len(schedule) == 1


def test_build_schedule_empty_when_no_pets():
    """Owner with no pets → empty schedule, no errors."""
    owner = Owner(name="Sam", age=25, gender="female", budget=200.0)
    scheduler = Scheduler(owner)
    assert scheduler.build_schedule(today=TODAY) == []


# ===========================================================================
# SCHEDULER — RECURRENCE LOGIC
# ===========================================================================

def test_complete_daily_task_spawns_next_day():
    """
    Completing a daily task should add a new copy with due_date = today + 1.

    timedelta(days=1) always gives tomorrow's date regardless of month
    boundaries or leap years, so this test drives the same logic as prod.
    """
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(title="Morning Walk", frequency="daily"))

    spawned = scheduler.complete_task("Mochi", "Morning Walk", today=TODAY)

    assert spawned is not None, "a new task should have been spawned"
    assert spawned.due_date == TODAY + timedelta(days=1)
    assert spawned.completed is False


def test_complete_weekly_task_spawns_seven_days_later():
    """
    Completing a weekly task should add a new copy with due_date = today + 7.

    timedelta(weeks=1) == timedelta(days=7) so the day-of-week is preserved.
    """
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(title="Bath", frequency="weekly"))

    spawned = scheduler.complete_task("Mochi", "Bath", today=TODAY)

    assert spawned is not None
    assert spawned.due_date == TODAY + timedelta(weeks=1)


def test_complete_once_task_does_not_spawn():
    """
    A one-off task (frequency="once") must NOT create a next occurrence.
    The task should stay completed forever.
    """
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(title="Vet Visit", frequency="once"))

    spawned = scheduler.complete_task("Mochi", "Vet Visit", today=TODAY)

    assert spawned is None, "once tasks must never spawn a follow-up"
    assert len(pet.tasks) == 1   # still only the original (completed) task


def test_reset_tasks_resets_daily_on_new_day():
    """
    reset_tasks() called on a new calendar day should mark daily tasks pending
    again.  Calling it twice on the same day must be idempotent.
    """
    scheduler, _, pet = make_scheduler()
    task = make_task(title="Morning Walk", frequency="daily")
    task.complete()
    pet.add_task(task)

    counts = scheduler.reset_tasks(today=TODAY + timedelta(days=1))

    assert counts["daily"] == 1
    assert task.completed is False


def test_reset_tasks_is_idempotent_same_day():
    """Calling reset_tasks twice on the same day should only reset once."""
    scheduler, _, pet = make_scheduler()
    task = make_task(title="Morning Walk", frequency="daily")
    task.complete()
    pet.add_task(task)

    scheduler.reset_tasks(today=TODAY)
    task.complete()                        # complete it again
    counts = scheduler.reset_tasks(today=TODAY)  # same day — should NOT reset

    assert counts["daily"] == 0
    assert task.completed is True   # still done because we didn't advance the day


def test_reset_tasks_does_not_reset_once_tasks():
    """frequency="once" tasks must remain completed after reset_tasks."""
    scheduler, _, pet = make_scheduler()
    task = make_task(title="Vet Visit", frequency="once")
    task.complete()
    pet.add_task(task)

    scheduler.reset_tasks(today=TODAY + timedelta(days=1))

    assert task.completed is True


def test_complete_walk_increases_pet_happiness():
    """Completing a walk task should trigger apply_walk() on the pet."""
    scheduler, _, pet = make_scheduler()
    pet.happiness_level = 50
    pet.add_task(make_task(title="Walk", task_type="walk", frequency="once"))

    scheduler.complete_task("Mochi", "Walk", today=TODAY)

    assert pet.happiness_level == 65


def test_complete_feed_increases_pet_fullness():
    """Completing a feed task should trigger apply_feeding() on the pet."""
    scheduler, _, pet = make_scheduler()
    pet.fullness = 50
    pet.add_task(make_task(title="Feed", task_type="feed", frequency="once"))

    scheduler.complete_task("Mochi", "Feed", today=TODAY)

    assert pet.fullness == 75


# ===========================================================================
# SCHEDULER — CONFLICT DETECTION
# ===========================================================================

def test_detect_conflicts_same_pet_overlap():
    """
    Two overlapping tasks on the SAME pet → SAME-PET warning.

    Overlap condition:  sA < eB  AND  sB < eA
    Here: Walk starts 08:00, ends 08:30.  Groom starts 08:15, ends 08:45.
    08:00 < 08:45  AND  08:15 < 08:30  → overlap confirmed.
    """
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(title="Walk",  scheduled_time="08:00", duration_minutes=30))
    pet.add_task(make_task(title="Groom", scheduled_time="08:15", duration_minutes=30))

    warnings = scheduler.detect_conflicts(today=TODAY)

    assert len(warnings) == 1
    assert "SAME-PET" in warnings[0]


def test_detect_conflicts_cross_pet_overlap():
    """
    Overlapping tasks on DIFFERENT pets → CROSS-PET warning.
    An owner cannot attend two animals simultaneously.
    """
    owner = Owner(name="Alex", age=30, gender="nonbinary", budget=500.0)
    mochi = Pet(name="Mochi", species="dog", fur_color="golden")
    luna  = Pet(name="Luna",  species="cat", fur_color="white")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    scheduler = Scheduler(owner)

    mochi.add_task(make_task(title="Walk",    scheduled_time="10:00", duration_minutes=30))
    luna.add_task( make_task(title="Feeding", scheduled_time="10:15", duration_minutes=30))

    warnings = scheduler.detect_conflicts(today=TODAY)

    assert len(warnings) == 1
    assert "CROSS-PET" in warnings[0]


def test_detect_conflicts_no_conflict_for_sequential_tasks():
    """
    Tasks that touch end-to-end (A ends at 09:00, B starts at 09:00) must NOT
    be flagged — the overlap test is strict: sA < eB AND sB < eA.
    When sB == eA the second condition fails (09:00 < 09:00 is False).
    """
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(title="Walk",  scheduled_time="08:00", duration_minutes=60))
    pet.add_task(make_task(title="Groom", scheduled_time="09:00", duration_minutes=30))

    warnings = scheduler.detect_conflicts(today=TODAY)

    assert warnings == []


def test_detect_conflicts_skips_unscheduled_tasks():
    """Tasks without a scheduled_time cannot overlap and must be ignored."""
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(title="Walk",          scheduled_time="08:00", duration_minutes=30))
    pet.add_task(make_task(title="No-time Groom", scheduled_time=None,    duration_minutes=30))

    warnings = scheduler.detect_conflicts(today=TODAY)

    assert warnings == []


def test_detect_conflicts_exact_same_start_time():
    """
    Two tasks starting at the exact same time are the clearest conflict case.
    Both the SAME-PET and the start==start condition should trigger a warning.
    """
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(title="Walk",  scheduled_time="09:00", duration_minutes=30))
    pet.add_task(make_task(title="Groom", scheduled_time="09:00", duration_minutes=20))

    warnings = scheduler.detect_conflicts(today=TODAY)

    assert len(warnings) >= 1


# ===========================================================================
# SCHEDULER — EDGE CASES
# ===========================================================================

def test_pet_with_no_tasks_returns_empty_schedule():
    """A pet that has no tasks should produce an empty schedule without errors."""
    scheduler, _, _ = make_scheduler()
    assert scheduler.build_schedule(today=TODAY) == []


def test_complete_task_unknown_pet_returns_none():
    """complete_task() for a non-existent pet name must return None gracefully."""
    scheduler, _, _ = make_scheduler()
    result = scheduler.complete_task("GhostDog", "Walk", today=TODAY)
    assert result is None


def test_complete_task_unknown_title_returns_none():
    """complete_task() for a title that doesn't exist must return None gracefully."""
    scheduler, _, pet = make_scheduler()
    pet.add_task(make_task(title="Walk"))
    result = scheduler.complete_task("Mochi", "NonexistentTask", today=TODAY)
    assert result is None


def test_get_tasks_for_unknown_pet_returns_empty_list():
    """get_tasks_for_pet() with an unrecognized name should return []."""
    scheduler, _, _ = make_scheduler()
    assert scheduler.get_tasks_for_pet("UnknownPet") == []


def test_filter_tasks_by_pet_name_isolates_one_pet():
    """filter_tasks(pet_name=...) should return only that pet's tasks."""
    owner = Owner(name="Alex", age=30, gender="nonbinary", budget=500.0)
    mochi = Pet(name="Mochi", species="dog", fur_color="golden")
    luna  = Pet(name="Luna",  species="cat", fur_color="white")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    scheduler = Scheduler(owner)

    mochi.add_task(make_task(title="Mochi Walk"))
    luna.add_task( make_task(title="Luna Feed"))

    results = scheduler.filter_tasks(pet_name="Mochi")
    assert all(pet.name == "Mochi" for pet, _ in results)
    assert len(results) == 1
