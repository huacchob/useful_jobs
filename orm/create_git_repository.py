secrets_group_name = "GIT"
remote_url = "https://github.com/huacchob/useful_jobs.git"
repo_name = "useful_jobs"
branch = "main"
provided_contents = ["extras.job"]

git_secrets_group = SecretsGroup.objects.get(name=secrets_group_name)

repo, _ = GitRepository.objects.get_or_create(
    name="useful_jobs",
    defaults={
        "remote_url": remote_url,
        "branch": branch,
        "secrets_group_id": git_secrets_group.id,
        "provided_contents": provided_contents,
    },
)
