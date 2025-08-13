import os
import subprocess
import git
import datetime


def _get_y_n(question: str) -> bool:
    """
    A basic wrapper for input() that asks the user a yes or no question and returns True or False based on their answer,
    prompting them further if they don't give correct responses.

    Args:
        question: The question to pose the user.

    Returns:
        bool: True if the user replied yes (Y/y), False if they replied no (N/n)
    """
    decision = input(f"{question} Y/N").upper()
    while decision not in ["Y", "N"]:
        decision = input(f"{question} Please enter only Y or N").upper()
    if decision == "N":
        return False
    else:
        return True


def tpar_check_dir() -> str | None:
    """
    A function which opening the file in which the path to the tpar directory is stored, checks whether it is empty,
    and reads the text inside it if it is not.

    Returns:
        The contents of tpar_directory.txt if they exist, or None if it is empty.

    """
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "tpar_directory.txt"), "r") as tpar_dir_file:
        # Get rid of unneeded whitespace
        tpar_dir = tpar_dir_file.read().strip()
        if len(tpar_dir) == 0:
            return None
        else:
            return tpar_dir


def tpar_set_dir(directory: str) -> None:
    """
    Ensures that the string provided is a valid path to a directory, then saves it as the directory in which to run all
    other TPAR related saving/loading commands.

    Args:
        directory: A path to the directory to set as the TPAR directory
    """
    # Make sure the user is alerted if they've already set this value
    existing_dir = tpar_check_dir()
    if existing_dir:
        if not _get_y_n(
            f"TPAR directory already set to {existing_dir}, do you wish to overwrite this?"
        ):
            print("Aborting")
            return

    # check they've actually given us a valid path
    directory = os.path.normpath(directory)
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return

    # show the user a list of the tpar files in this directory to check that they've got the right one
    files = [f for f in os.listdir(directory) if f.lower().endswith(".tpar")]
    print(f"TPAR files in {directory}:\n{'\n'.join(files)}\n")
    if not _get_y_n("Is this the folder you would like to select?"):
        print("Please double check your directory path and try again.")
        return

    # If it isn't already set up as a git repo, do so. If it is, and it's set up to track a remote, print a big warning.
    try:
        repo = git.Repo(directory)
        try:
            remote = repo.remote()
            print(
                f"WARNING: This directory is already in a repository at {repo.working_tree_dir}, set up to track "
                f"{remote.url}.\nYou are advised not to run save/load commands in this repository, as it will interfere with"
                f" other files stored here."
            )
        except ValueError:
            pass
    except git.InvalidGitRepositoryError:
        git.Repo.init(directory)

    # save this directory for use in all future tpar commands
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "tpar_directory.txt"), "w") as tpar_dir_file:
        tpar_dir_file.write(directory)

    print(f"TPAR directory set to {directory}")


def tpar_save_state(tag_name: None | str = None) -> None:
    """
    Commits all changes in the TPAR directory and tags the commit.

    Args:
        tag_name (optional): What to name the tag (also used as commit message). If None, jst uses the ISO format of the
            current UTC time
    """
    if tag_name is None:
        time_now = datetime.datetime.now(datetime.timezone.utc)
        tag_name = time_now.strftime("%Y-%m-%dT%H-%M-%S")

    directory = tpar_check_dir()
    if directory is None:
        print(
            "No TPAR directory set, please use tpar_set_dir(<directory>) first to continue."
        )
        return

    repo = git.Repo(directory)
    repo.git.add(all=True)
    repo.index.commit(tag_name)
    repo.create_tag(tag_name)


def tpar_show_saves() -> None:
    """
    Prints all tag names in the TPAR directory
    """
    directory = tpar_check_dir()
    if directory is None:
        print(
            "No TPAR directory set, please use tpar_set_dir(<directory>) first to continue."
        )
        return

    repo = git.Repo(directory)
    commit_messages = [str(t.commit.message) for t in repo.tags]
    print(
        f"The following saved directory states are available:\n{'\n'.join(commit_messages)}"
    )


def tpar_load_save(save_name: str) -> None:
    """
    Restores any modified files to the state they were in at the time of a specified tag. Does not alter files that have
    been created since that tag.

    Args:
        save_name: The name if the tag to load.
    """
    directory = tpar_check_dir()
    if directory is None:
        print(
            "No TPAR directory set, please use tpar_set_dir(<directory>) first to continue."
        )
        return

    repo = git.Repo(directory)
    # First check that the supplied tag exists
    try:
        save_tag = [t for t in repo.tags if t.commit.message == save_name][0]
    except IndexError:
        print(
            "No save/tag under that name, consider using tpar_show_saves and trying again."
        )
        return

    # Make sure that everything committed in advance of the rollback, just in case it needs to be reverted. Just use
    # current ISO datetime for this.
    time_now = datetime.datetime.now(datetime.timezone.utc)
    commit_name = time_now.isoformat()
    repo.git.add(all=True)
    repo.index.commit(commit_name)

    # The goal is to load the state of their "main" files as they were at the old tag. As such, we're not deleting any
    # new files created as discrete copies of them, and only rolling back files that existed in the old tag.
    subprocess.run(f"git checkout {save_tag.commit.message} -- .", cwd=directory)

    print(f"Successfully loaded file states as of {save_name}")


def tpar_load_latest_save() -> None:
    """
    Restores any modified files to the state they were in at the time of the most recent tag. Does not alter files that
    have been created since that tag.
    """
    directory = tpar_check_dir()
    if directory is None:
        print(
            "No TPAR directory set, please use tpar_set_dir(<directory>) first to continue."
        )
        return
    repo = git.Repo(directory)

    # Make sure that everything committed in advance of the rollback, just in case it needs to be reverted. Just use
    # current ISO datetime for this.
    time_now = datetime.datetime.now(datetime.timezone.utc)
    commit_name = time_now.isoformat()
    repo.git.add(all=True)
    repo.index.commit(commit_name)

    # Search for the latest tag by just running a max() against the datetime objects attached to their commits
    save_tag = max(repo.tags, key=lambda t: t.commit.committed_datetime)
    # The goal is to load the state of their "main" files as they were at the old tag. As such, we're not deleting any
    # new files created as discrete copies of them, and only rolling back files that existed in the old tag.
    subprocess.run(f"git checkout {save_tag.commit.message} -- .", cwd=directory)

    # Let the user know what the tag was called, in case they were expecting something else.
    print(f"Successfully loaded file states as of the latest git tag, {save_tag}")
