from pawpal_system import Task, Pet, Owner, Scheduler

# --- Create owner ---
owner = Owner(name="Jordan", age=28, gender="non-binary", budget=200.0)

# --- Create pets ---
mochi = Pet(name="Mochi", species="dog", fur_color="golden")
luna  = Pet(name="Luna",  species="cat", fur_color="black")

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Add tasks to Mochi ---
mochi.add_task(Task(
    title="Morning Walk",
    description="30-minute walk around the block",
    duration_minutes=30,
    priority="high",
    task_type="walk",
    frequency="daily",
))
mochi.add_task(Task(
    title="Breakfast",
    description="One cup of dry kibble",
    duration_minutes=5,
    priority="high",
    task_type="feed",
    frequency="daily",
))

# --- Add tasks to Luna ---
luna.add_task(Task(
    title="Wet Food Dinner",
    description="Half a can of wet food",
    duration_minutes=5,
    priority="medium",
    task_type="feed",
    frequency="daily",
))
luna.add_task(Task(
    title="Brush Coat",
    description="Gentle brush to reduce shedding",
    duration_minutes=10,
    priority="low",
    task_type="groom",
    frequency="weekly",
))

# --- Run scheduler ---
scheduler = Scheduler(owner)
print(scheduler.explain_plan())

# --- Mark one task complete and show the effect ---
print("\n-- Completing 'Morning Walk' for Mochi --")
scheduler.complete_task("Mochi", "Morning Walk")
print(mochi.get_status())

print("\n-- Updated schedule --")
print(scheduler.explain_plan())
