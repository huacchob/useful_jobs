from nautobot.extras.models import (
    GitRepository,
    Secret,
    SecretsGroup,
    SecretsGroupAssociation,
)

secret1 = "GIT_USERNAME"
secret2 = "GIT_SECRET"
provider = "environment-variable"
secrets_group_name = "GIT"
sga_access_type = "HTTP(S)"
sga1_secret_type = "username"
sga2_secret_type = "token"
remote_url = "https://github.com/huacchob/useful_jobs.git"
repo_name = "useful_jobs"
branch = "main"
provided_contents = ["extras.job"]

s1, _ = Secret.objects.get_or_create(
    name=secret1,
    provider=provider,
    parameters={"variable": secret1},
)
s2, _ = Secret.objects.get_or_create(
    name=secret2,
    provider=provider,
    parameters={"variable": secret2},
)

sg, _ = SecretsGroup.objects.get_or_create(
    name=secrets_group_name,
)

sga1, _ = SecretsGroupAssociation.objects.get_or_create(
    secret=s1,
    access_type=sga_access_type,
    secret_type=sga1_secret_type,
    secrets_group=sg,
)
sga2, _ = SecretsGroupAssociation.objects.get_or_create(
    secret=s1,
    access_type=sga_access_type,
    secret_type=sga2_secret_type,
    secrets_group=sg,
)

sg.validated_save()

repo, _ = GitRepository.objects.get_or_create(
    name=repo_name,
    defaults={
        "remote_url": remote_url,
        "branch": branch,
        "secrets_group_id": sg.id,
        "provided_contents": provided_contents,
    },
)

repo.save()
