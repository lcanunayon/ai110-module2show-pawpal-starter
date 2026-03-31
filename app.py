import streamlit as st
from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session state — initialised once per browser session
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", age=28, gender="non-binary", budget=200.0)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

owner: Owner     = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption(f"Owner: {owner.name}  |  Budget: ${owner.budget:.2f}")
st.divider()


# ===========================================================================
# Section 1 — Add a Pet
# ===========================================================================
st.subheader("Add a Pet")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name  = st.text_input("Pet name",  value="Mochi")
    with col2:
        species   = st.selectbox("Species", ["dog", "cat", "other"])
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

if owner.pets:
    st.markdown("**Your pets:**")
    for pet in owner.pets:
        st.write(f"- {pet.get_status()}")
else:
    st.info("No pets yet. Add one above.")

st.divider()


# ===========================================================================
# Section 2 — Schedule a Task
# ===========================================================================
st.subheader("Schedule a Task")

if not owner.pets:
    st.warning("Add a pet first before scheduling tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_options       = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("Choose a pet", pet_options)

        col1, col2 = st.columns(2)
        with col1:
            task_title   = st.text_input("Task title",  value="Morning Walk")
            task_type    = st.selectbox("Task type", ["walk", "feed", "groom", "vet", "other"])
            priority     = st.selectbox("Priority",  ["low", "medium", "high"], index=2)
            frequency    = st.selectbox("Frequency", ["daily", "weekly", "once"])
        with col2:
            description     = st.text_input("Description", value="")
            duration        = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            scheduled_time  = st.text_input(
                "Scheduled time (HH:MM, 24-h)", value="",
                help="Leave blank if the time is flexible. Example: 08:00"
            )
            due_date_input  = st.date_input("Due date", value=date.today())

        task_submitted = st.form_submit_button("Add Task")

    if task_submitted:
        # Validate optional time field
        time_value = scheduled_time.strip() if scheduled_time.strip() else None
        if time_value:
            parts = time_value.split(":")
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                st.error("Scheduled time must be in HH:MM format (e.g. 08:30).")
                time_value = None

        target_pet = owner.get_pet(selected_pet_name)
        new_task = Task(
            title=task_title.strip(),
            description=description.strip(),
            duration_minutes=int(duration),
            priority=priority,
            task_type=task_type,
            frequency=frequency,
            scheduled_time=time_value,
            due_date=due_date_input,
        )
        target_pet.add_task(new_task)
        st.success(f"Scheduled '{new_task.title}' for {target_pet.name}.")

st.divider()


# ===========================================================================
# Section 3 — Today's Schedule  (sorted + conflict warnings)
# ===========================================================================
st.subheader("Today's Schedule")

today = date.today()
col_gen, col_reset = st.columns([3, 1])
with col_gen:
    generate = st.button("Generate Schedule", use_container_width=True)
with col_reset:
    reset_btn = st.button("Reset Daily Tasks", use_container_width=True)

if reset_btn:
    counts = scheduler.reset_tasks(today=today)
    st.success(f"Reset {counts['daily']} daily task(s) and {counts['weekly']} weekly task(s).")

if generate:
    if not owner.pets:
        st.warning("Add a pet and some tasks first.")
    else:
        # --- Conflict detection (shown BEFORE the schedule table) ---
        conflicts = scheduler.detect_conflicts(today=today)
        if conflicts:
            st.error(
                f"⚠️ **{len(conflicts)} scheduling conflict(s) detected.** "
                "Resolve these before your day starts:"
            )
            for warn in conflicts:
                # Parse the conflict type for a friendlier label
                if "SAME-PET" in warn:
                    icon = "🐾"
                    msg  = warn.replace("WARNING [SAME-PET] ", "")
                    st.warning(f"{icon} **Same-pet conflict:** {msg}")
                else:
                    icon = "👤"
                    msg  = warn.replace("WARNING [CROSS-PET] ", "")
                    st.warning(f"{icon} **Your attention is double-booked:** {msg}")
        else:
            st.success("✅ No scheduling conflicts — your day is clear!")

        # --- Build and display the sorted schedule ---
        plan = scheduler.build_schedule(today=today)
        if not plan:
            st.info("No pending tasks due today — everything is done!")
        else:
            st.markdown(f"**{len(plan)} task(s) for today** — sorted by time → priority → duration:")

            # Build a table-friendly list of dicts
            rows = []
            for pet, task in plan:
                rows.append({
                    "Pet":        pet.name,
                    "Time":       task.scheduled_time if task.scheduled_time else "—",
                    "Task":       task.title,
                    "Type":       task.task_type,
                    "Priority":   task.priority,
                    "Duration":   f"{task.duration_minutes} min",
                    "Frequency":  task.frequency,
                    "Status":     "✅ done" if task.completed else "⏳ pending",
                })

            st.table(rows)

st.divider()


# ===========================================================================
# Section 4 — Filter & Browse Tasks
# ===========================================================================
st.subheader("Browse Tasks")

if not owner.pets:
    st.info("No tasks yet.")
else:
    col_pet, col_status = st.columns(2)
    with col_pet:
        filter_pet = st.selectbox(
            "Filter by pet", ["All pets"] + [p.name for p in owner.pets]
        )
    with col_status:
        filter_status = st.selectbox(
            "Filter by status", ["all", "pending", "completed"]
        )

    pet_arg    = None if filter_pet == "All pets" else filter_pet
    status_arg = filter_status

    filtered = scheduler.filter_tasks(pet_name=pet_arg, status=status_arg)

    if not filtered:
        st.info("No tasks match that filter.")
    else:
        rows = []
        for pet, task in filtered:
            rows.append({
                "Pet":       pet.name,
                "Task":      task.title,
                "Type":      task.task_type,
                "Priority":  task.priority,
                "Time":      task.scheduled_time if task.scheduled_time else "—",
                "Duration":  f"{task.duration_minutes} min",
                "Frequency": task.frequency,
                "Status":    "✅ done" if task.completed else "⏳ pending",
            })
        st.table(rows)

st.divider()


# ===========================================================================
# Section 5 — Mark a Task Complete
# ===========================================================================
st.subheader("Mark a Task Complete")

all_pending = scheduler.get_all_pending(today=today)
if not all_pending:
    st.info("No pending tasks to mark complete.")
else:
    options = {
        f"{pet.name}: {task.title}": (pet.name, task.title)
        for pet, task in all_pending
    }
    chosen = st.selectbox("Select a task to complete", list(options.keys()))

    if st.button("Mark Complete"):
        pet_n, task_t = options[chosen]
        spawned = scheduler.complete_task(pet_n, task_t, today=today)
        pet = owner.get_pet(pet_n)
        st.success(f"Completed '{task_t}' for {pet_n}!")
        st.write(pet.get_status())
        if spawned is not None:
            st.info(
                f"🔁 Next occurrence of '{spawned.title}' scheduled for "
                f"**{spawned.due_date}** ({spawned.frequency})."
            )
