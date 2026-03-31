from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler

TODAY = date(2026, 3, 30)


def run_conflict_check(label: str, scheduler: Scheduler):
    """Print a clearly labelled conflict report for today's schedule."""
    print(f"\n{'=' * 62}")
    print(f"CONFLICT CHECK -- {label}")
    print("=" * 62)
    warnings = scheduler.detect_conflicts(today=TODAY)
    if warnings:
        for w in warnings:
            print(f"  {w}")
    else:
        print("  OK -- no conflicts detected.")


# ===========================================================================
# SCENARIO 1: Clean schedule — no overlaps
# ===========================================================================
print("\n" + "=" * 62)
print("SCENARIO 1: Clean schedule (no overlapping tasks)")
print("=" * 62)

owner1 = Owner(name="Jordan", age=28, gender="non-binary", budget=200.0)
mochi1 = Pet(name="Mochi", species="dog", fur_color="golden")
luna1  = Pet(name="Luna",  species="cat", fur_color="black")
owner1.add_pet(mochi1)
owner1.add_pet(luna1)

mochi1.add_task(Task("Morning Walk",  "Around the block", 30, "high", "walk",  "daily",  "07:00", due_date=TODAY))
mochi1.add_task(Task("Breakfast",     "Dry kibble",        5, "high", "feed",  "daily",  "08:00", due_date=TODAY))
luna1.add_task( Task("Lunchtime Nap", "Sunny windowsill", 60, "low",  "other", "daily",  "12:00", due_date=TODAY))
luna1.add_task( Task("Wet Food",      "Half a can",        5, "med",  "feed",  "daily",  "18:00", due_date=TODAY))

s1 = Scheduler(owner1)
print("  Tasks scheduled today:")
for pet, task in s1.sort_by_time(s1.get_all_pending(today=TODAY)):
    print(f"    {pet.name:6} | {task.scheduled_time} +{task.duration_minutes:>3}min | {task.title}")
run_conflict_check("Scenario 1", s1)


# ===========================================================================
# SCENARIO 2: Same-pet conflict
# A pet cannot be walked and given a bath at the same time.
#
# Morning Walk starts at 07:00 and lasts 30 min  -> window 07:00-07:30
# Quick Bath    starts at 07:15 and lasts 20 min  -> window 07:15-07:35
# These windows overlap by 15 minutes.
# ===========================================================================
print("\n" + "=" * 62)
print("SCENARIO 2: Same-pet conflict (Mochi has two tasks at once)")
print("=" * 62)

owner2 = Owner(name="Jordan", age=28, gender="non-binary", budget=200.0)
mochi2 = Pet(name="Mochi", species="dog", fur_color="golden")
owner2.add_pet(mochi2)

mochi2.add_task(Task("Morning Walk", "Around the block", 30, "high", "walk",  "daily", "07:00", due_date=TODAY))
mochi2.add_task(Task("Quick Bath",   "Rinse and dry",    20, "med",  "groom", "once",  "07:15", due_date=TODAY))  # overlaps!
mochi2.add_task(Task("Breakfast",    "Dry kibble",        5, "high", "feed",  "daily", "08:00", due_date=TODAY))  # no conflict

s2 = Scheduler(owner2)
print("  Tasks scheduled today:")
for pet, task in s2.sort_by_time(s2.get_all_pending(today=TODAY)):
    print(f"    {pet.name:6} | {task.scheduled_time} +{task.duration_minutes:>3}min | {task.title}")
run_conflict_check("Scenario 2", s2)


# ===========================================================================
# SCENARIO 3: Cross-pet conflict
# The owner cannot groom Luna and walk Mochi at the same time.
#
# Mochi Evening Walk starts 18:00, lasts 30 min  -> window 18:00-18:30
# Luna  Brush Coat    starts 18:20, lasts 10 min  -> window 18:20-18:30
# These overlap by 10 minutes.
# ===========================================================================
print("\n" + "=" * 62)
print("SCENARIO 3: Cross-pet conflict (owner cannot attend two pets at once)")
print("=" * 62)

owner3 = Owner(name="Jordan", age=28, gender="non-binary", budget=200.0)
mochi3 = Pet(name="Mochi", species="dog", fur_color="golden")
luna3  = Pet(name="Luna",  species="cat", fur_color="black")
owner3.add_pet(mochi3)
owner3.add_pet(luna3)

mochi3.add_task(Task("Morning Walk",    "Around the block",  30, "high", "walk",  "daily",  "07:00", due_date=TODAY))  # no conflict
mochi3.add_task(Task("Evening Walk",    "Park route",        30, "high", "walk",  "daily",  "18:00", due_date=TODAY))  # overlaps Luna
luna3.add_task( Task("Lunchtime Treat", "Small kibble snack", 5, "med",  "feed",  "daily",  "12:00", due_date=TODAY))  # no conflict
luna3.add_task( Task("Brush Coat",      "Reduce shedding",   10, "low",  "groom", "weekly", "18:20", due_date=TODAY))  # overlaps Mochi!

s3 = Scheduler(owner3)
print("  Tasks scheduled today:")
for pet, task in s3.sort_by_time(s3.get_all_pending(today=TODAY)):
    print(f"    {pet.name:6} | {task.scheduled_time} +{task.duration_minutes:>3}min | {task.title}")
run_conflict_check("Scenario 3", s3)


# ===========================================================================
# SCENARIO 4: Multiple conflicts at once
# ===========================================================================
print("\n" + "=" * 62)
print("SCENARIO 4: Multiple conflicts in one schedule")
print("=" * 62)

owner4 = Owner(name="Jordan", age=28, gender="non-binary", budget=200.0)
mochi4 = Pet(name="Mochi", species="dog", fur_color="golden")
luna4  = Pet(name="Luna",  species="cat", fur_color="black")
owner4.add_pet(mochi4)
owner4.add_pet(luna4)

# Same-pet clash for Mochi: Walk 07:00+30 overlaps Bath 07:20+15
mochi4.add_task(Task("Morning Walk", "Around the block", 30, "high", "walk",  "daily", "07:00", due_date=TODAY))
mochi4.add_task(Task("Quick Bath",   "Rinse and dry",    15, "med",  "groom", "once",  "07:20", due_date=TODAY))
# Cross-pet clash: Mochi Vet 10:00+60 overlaps Luna Vet 10:30+30
mochi4.add_task(Task("Vet Visit",    "Annual check",     60, "high", "vet",   "once",  "10:00", due_date=TODAY))
luna4.add_task( Task("Vet Visit",    "Booster shot",     30, "high", "vet",   "once",  "10:30", due_date=TODAY))
# Clean tasks — no conflicts
mochi4.add_task(Task("Breakfast",    "Dry kibble",        5, "high", "feed",  "daily", "08:00", due_date=TODAY))
luna4.add_task( Task("Wet Food",     "Half a can",        5, "med",  "feed",  "daily", "18:00", due_date=TODAY))

s4 = Scheduler(owner4)
print("  Tasks scheduled today:")
for pet, task in s4.sort_by_time(s4.get_all_pending(today=TODAY)):
    print(f"    {pet.name:6} | {task.scheduled_time} +{task.duration_minutes:>3}min | {task.title}")
run_conflict_check("Scenario 4", s4)
