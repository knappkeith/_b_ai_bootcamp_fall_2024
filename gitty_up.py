import os
from random import choice
import subprocess

from git import Repo
from openai import AzureOpenAI

NL = "\n"


def copy_to_clipboard(bytes_data):
    """Copy the given bytes to the clipboard."""
    process = subprocess.Popen('pbcopy', stdin=subprocess.PIPE)
    process.communicate(bytes_data)
    process.wait()


def git_stuff(repo: str):
    """Obtains the changes between two branches"""

    repo = Repo(repo)

    # Get the main branch
    main_branch_name = input(
        "Please Select the branch you want to merge into (default: main):"
        f"\n{NL.join([f'    - {x}' for x in repo.heads])}\n"
    )
    if main_branch_name == "":
        main_branch_name = "main"
    main_branch = [x for x in repo.heads if str(x) == main_branch_name][0]

    # Get the PR branch
    pr_branch_name = input(
        "Please Select the branch you want to create the PR from "
        f"(default: {repo.active_branch}):\n"
        f"{NL.join([f'    - {x}' for x in repo.heads if str(x) != main_branch_name])}\n"
    )
    if pr_branch_name == "":
        pr_branch = repo.active_branch
        pr_branch_name = str(repo.active_branch)
    else:
        pr_branch = [x for x in repo.heads if str(x) == pr_branch_name][0]

    # Get the differences
    diff = main_branch.commit.diff(pr_branch.commit, create_patch=True)
    list_changes = [item.diff.decode("utf-8") for item in diff]
    print(
        f"You have selected {pr_branch_name} --> {main_branch_name}, there are a "
        f"total of {len(list_changes)} changes."
    )
    return list_changes


def summarize(content: str, client: AzureOpenAI):
    """Uses openAI to summarize"""
    conversation = [
        {
            "role": "system",
            "content": content
        },
    ]
    response = client.chat.completions.create(
        model="gpt-35-turbo",
        messages=conversation
    )
    response_msg = choice(response.choices)
    output_msg = response_msg.message.content
    return output_msg


def main():
    """Main function of the Generator"""
    print(
        "Welcome to Gitty Up (Cara's idea not mine), a helpful tool to generate PR "
        "Comments for your changes."
    )
    repo = input("\nPlease enter the path to your Git Repo: ")

    client = AzureOpenAI(
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01"
    )
    git_changes = git_stuff(repo=repo)

    # change_summaries = [
    #     summarize(
    #         "You are a code examiner. Please summarize each of the changes in "
    #         "this list of changes and only include important changes and make "
    #         f"the list of changes very concise:  {x}",
    #         client=client
    #     ) for x in git_changes
    # ]
    change_summaries = [
        summarize(
            "You are a code examiner. Please summarize each of the changes in "
            "this list of changes and make "
            f"the list of changes very concise:  {NL}{NL.join(git_changes)}",
            client=client
        )
    ]
    full_list_o_change_summeries = "\n".join(change_summaries)
    overall_summary = summarize(
        "Please summarize this list into a concise single sentence summary: "
        f"{full_list_o_change_summeries}",
        client=client
    )

    # CODE HERE FOR GENERATING IMAGE
    cute_image_binary = b''

    print("\nShort Summary of changes:")
    print(overall_summary)
    print("\nFull list of changes:")
    print(full_list_o_change_summeries)
    print("\nCute Binary:")
    print(cute_image_binary)

    clipboard_array = ["## Summary".encode("utf-8")]
    clipboard_array.append(overall_summary.encode("utf-8"))
    clipboard_array.append("".encode("utf-8"))
    clipboard_array.append("## Descriptions of Changes".encode("utf-8"))
    clipboard_array.append(
        "\n".join(change_summaries).encode("utf-8")
    )
    clipboard_array.append("".encode("utf-8"))
    clipboard_array.append("## CUTE".encode("utf-8"))
    clipboard_array.append(cute_image_binary)

    # Put into clipboard
    copy_to_clipboard(NL.encode("utf-8").join(clipboard_array))

    print("\n\nYour Change Summary and Image has been placed in your clipboard.")

main()
