from nautobot.extras.models import (
    GitRepository,
    Secret,
    SecretsGroup,
    SecretsGroupAssociation,
)

secret1 = "GIT_USERNAME"
secret2 = "GIT_SECRET"
secrets_group_name = "GIT"
remote_url = "https://github.com/huacchob/useful_jobs.git"
repo_name = "useful_jobs"
branch = "main"
provided_contents = ["extras.job"]

s1, _ = Secret.objects.get_or_create(
    name=secret1,
    provider="environment-variable",
    parameters={"variable": secret1},
)
s2, _ = Secret.objects.get_or_create(
    name=secret2,
    provider="environment-variable",
    parameters={"variable": secret2},
)

sg, _ = SecretsGroup.objects.get_or_create(
    name=secrets_group_name,
)

sga1, _ = SecretsGroupAssociation.objects.get_or_create(
    secret=s1,
    access_type="HTTP(S)",
    secret_type="username",
    secrets_group=sg,
)
sga2, _ = SecretsGroupAssociation.objects.get_or_create(
    secret=s1,
    access_type="HTTP(S)",
    secret_type="token",
    secrets_group=sg,
)

sg.validated_save()

repo, _ = GitRepository.objects.get_or_create(
    name="useful_jobs",
    defaults={
        "remote_url": remote_url,
        "branch": branch,
        "secrets_group_id": sg.id,
        "provided_contents": provided_contents,
    },
)
