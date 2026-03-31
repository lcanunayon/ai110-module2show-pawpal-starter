import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state initialization ---
# Only runs once per session; subsequent reruns skip over these blocks.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", age=28, gender="non-binary", budget=200.0)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption(f"Owner: {owner.name}  |  Budget: ${owner.budget:.2f}")

st.divider()

# ---------------------------------------------------------------------------
# Section 1: Add a Pet
# ---------------------------------------------------------------------------
st.subheader("Add a Pet")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        fur_color = st.text_input("Fur color", value="golden")
    submitted = st.form_submit_button("Add Pet")

if submitted:
    if pet_name.strip():
        new_pet = Pet(name=pet_name.strip(), species=species, fur_color=fur_color.strip())
        owner.add_pet(new_pet)
        st.success(f"Added {new_pet.name} the {species}!")
    else:
        st.error("Pet name cannot be empty.")

# Show current pets
if owner.pets:
    st.markdown("**Your pets:**")
    for pet in owner.pets:
        st.write(f"- {pet.get_status()}")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add a Task to a Pet
# ---------------------------------------------------------------------------
st.subheader("Schedule a Task")

if not owner.pets:
    st.warning("Add a pet first before scheduling tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_options = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("Choose a pet", pet_options)

        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task title", value="Morning Walk")
            task_type = st.selectbox("Task type", ["walk", "feed", "groom", "vet", "other"])
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col2:
            description = st.text_input("Description", value="")
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

        task_submitted = st.form_submit_button("Add Task")

    if task_submitted:
        target_pet = owner.get_pet(selected_pet_name)
        new_task = Task(
            title=task_title.strip(),
            description=description.strip(),
            duration_minutes=int(duration),
            priority=priority,
            task_type=task_type,
            frequency=frequency,
        )
        target_pet.add_task(new_task)
        st.success(f"Scheduled '{new_task.title}' for {target_pet.name}.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Generate Schedule
# ---------------------------------------------------------------------------
st.subheader("Today's Schedule")

if st.button("Generate Schedule"):
    if not owner.pets:
        st.warning("Add a pet and some tasks first.")
    else:
        plan = scheduler.build_schedule()
        if not plan:
            st.info("No pending tasks — everything is done!")
        else:
            st.success("Here's today's plan, sorted by priority:")
            for pet, task in plan:
                st.markdown(f"**{pet.name}** — {task.describe()}")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Complete a Task
# ---------------------------------------------------------------------------
st.subheader("Mark a Task Complete")

all_pending = scheduler.get_all_pending()
if not all_pending:
    st.info("No pending tasks to mark complete.")
else:
    options = {f"{pet.name}: {task.title}": (pet.name, task.title) for pet, task in all_pending}
    chosen = st.selectbox("Select a task to complete", list(options.keys()))

    if st.button("Mark Complete"):
        pet_n, task_t = options[chosen]
        scheduler.complete_task(pet_n, task_t)
        pet = owner.get_pet(pet_n)
        st.success(f"Completed '{task_t}'!")
        st.write(pet.get_status())
