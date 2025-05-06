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

# Repo
useful_job: dict[str, str | list[str]] = {
    "remote_url": "https://github.com/huacchob/useful_jobs.git",
    "repo_name": "useful_jobs",
    "branch": "main",
    "provided_contents": ["extras.job"],
}
gc_mono: dict[str, str | list[str]] = {
    "remote_url": "https://github.com/huacchob/gc_mono.git",
    "repo_name": "gc_mono",
    "branch": "main",
    "provided_contents": [
        'extras.configcontext',
        'nautobot_golden_config.backupconfigs',
        'nautobot_golden_config.intendedconfigs',
        'nautobot_golden_config.jinjatemplate',
        'nautobot_golden_config.pluginproperties',
    ],
}
repos: list[dict[str, str | list[str]]] = [useful_job, gc_mono]

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
    secret=s2,
    access_type=sga_access_type,
    secret_type=sga2_secret_type,
    secrets_group=sg,
)

sg.validated_save()

for repo in repos:
    rp, _ = GitRepository.objects.get_or_create(
        name=repo.get("repo_name"),
        defaults={
            "remote_url": repo.get("remote_url"),
            "branch": repo.get("branch"),
            "secrets_group_id": sg.id,
            "provided_contents": repo.get("provided_contents"),
        },
    )

    rp.save()
