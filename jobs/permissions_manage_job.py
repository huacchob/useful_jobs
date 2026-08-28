"""Nautobot Job that reconciles Groups and ObjectPermissions from a YAML file.

``permissions.yml``, sitting next to this module, is the source of truth. Running
the job creates missing groups, creates missing permissions, and updates existing
permissions whose actions, models, constraints or group assignments have drifted.

Permission names carry the app label and the actions, so neither is repeated in
the file: ``<APP_LABEL>_<ACTIONS>`` where V=view, A=add, C=change, D=delete, in
that order. ``DCIM_V`` means view on the ``dcim`` app; ``IPAM_VACD`` means all
four actions on ``ipam``.
"""

from pathlib import Path
from typing import Any

import yaml
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from nautobot.apps.jobs import DryRunVar, Job, register_jobs
from nautobot.users.models import ObjectPermission

name = "Permissions Management"  # pylint: disable=invalid-name

PERMISSIONS_FILE = Path(__file__).resolve().parent / "permissions.yml"

#: Name suffix letters, in the order they must appear, mapped to their action.
ACTIONS_BY_LETTER = {"V": "view", "A": "add", "C": "change", "D": "delete"}


class PermissionsDefinitionError(Exception):
    """Raised when the YAML definition is invalid."""


def validate_yaml_file() -> dict[str, Any]:
    """Validate the file being ingested is a YAML file and is a dict.

    Raises:
        PermissionsDefinitionError: File not found.
        PermissionsDefinitionError: File can't be parsed as a YAML file.
        PermissionsDefinitionError: Top level YAML file is not a dictionary.

    Returns:
        dict[str, Any]: YAML file content.
    """
    if not PERMISSIONS_FILE.is_file():
        raise PermissionsDefinitionError(f"Permissions file not found at {PERMISSIONS_FILE}.")

    try:
        document: dict[str, Any] = yaml.safe_load(PERMISSIONS_FILE.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise PermissionsDefinitionError(f"Unable to parse {PERMISSIONS_FILE.name}: {error}") from error

    if not isinstance(document, dict):
        raise PermissionsDefinitionError("Top level of the YAML file must be a mapping.")
    return document


def validate_actions(action_letters: str, permission_name: str) -> list[str]:
    """Split a permission name into its app label and its actions.

    Args:
        action_letters: Permission action such as ``V``, ``VA``, ``VAC``, ``VACD``.
        permission_name: The name of the permission.

    Returns:
        A list of actions ``['V']`` or ``['V', 'A', 'C', 'D']``.

    Raises:
        PermissionsDefinitionError: If the name does not follow the convention.
    """
    unknown = sorted(set(action_letters) - set(ACTIONS_BY_LETTER))
    if unknown:
        raise PermissionsDefinitionError(
            f"Permission {permission_name} has unknown action letter(s) {unknown}. Valid letters are V, A, C, D."
        )

    expected = "".join(letter for letter in ACTIONS_BY_LETTER if letter in action_letters)
    if action_letters != expected:
        raise PermissionsDefinitionError(
            f"Permission {permission_name} lists its actions as '{action_letters}'; they must read '{expected}' "
            "(VACD order, no repeats)."
        )

    return [ACTIONS_BY_LETTER[letter] for letter in action_letters]


def resolve_object_types(app_label: str, models: Any, permission_name: str) -> list[ContentType]:
    """Resolve model names against the permission's app label.

    Args:
        app_label: App label taken from the permission name.
        models: The ``models`` list from the YAML file.
        permission_name: Used in error messages.

    Returns:
        The matching ContentType objects.

    Raises:
        PermissionsDefinitionError: If ``models`` is malformed or a model does
            not exist in the app.
    """
    if not isinstance(models, list) or not models:
        raise PermissionsDefinitionError(f"Permission '{permission_name}': 'models' must be a non-empty list.")

    object_types = []
    for model in models:
        if not isinstance(model, str) or "." in model:
            raise PermissionsDefinitionError(
                f"Permission '{permission_name}': '{model}' must be a bare model name; "
                f"the app label '{app_label}' comes from the permission name."
            )
        try:
            object_types.append(ContentType.objects.get_by_natural_key(app_label, model.lower()))
        except ContentType.DoesNotExist as error:
            raise PermissionsDefinitionError(
                f"Permission '{permission_name}': '{app_label}.{model}' is not an installed model."
            ) from error
    return object_types


def normalize_constraints(constraints: Any) -> dict | list | None:
    """Normalize the several ways of spelling "no constraint" to ``None``.

    Args:
        constraints: Raw constraints from YAML or from the database.

    Returns:
        ``None``, a mapping, or a list of mappings.
    """
    return constraints or None


class ManagePermissionsFromYAML(Job):  # pylint: disable=abstract-method
    """Reconcile Nautobot Groups and ObjectPermissions against permissions.yml."""

    dryrun = DryRunVar(description="Log the changes that would be made, then roll them back.")

    class Meta:
        """Job metadata."""

        name = "Manage Permissions from YAML"
        description = "Create and update Groups and ObjectPermissions so they match a git-managed YAML file."
        has_sensitive_variables = False

    def validate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Validate individual permission entries, and fail fast.

        Args:
            entry (dict[str: Any]): Raw permission fields from the YAML file individual permission entries.

        Returns:
            dict[str, Any]: A dictionary of the validated ObjectPermission parameters.
        """
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise PermissionsDefinitionError("Every entry under 'permissions' must be a mapping with a 'name'.")
        if not entry.get("name") or not isinstance(entry["name"], str):
            raise PermissionsDefinitionError("Permission name should be a string.")
        permission_name = entry["name"]
        if not isinstance(entry.get("groups"), list):
            raise PermissionsDefinitionError(f"Permission '{permission_name}': 'groups' must be a list.")
        permission_groups = entry["groups"]
        if not entry.get("app") or not isinstance(entry["app"], str):
            raise PermissionsDefinitionError(f"Permission '{permission_name}': 'app' must be a string.")
        app_label = entry["app"]
        if not isinstance(entry["action"], str):
            raise PermissionsDefinitionError(f"Permission '{permission_name}': 'actions' must be a string.")
        actions = validate_actions(entry["action"], permission_name)
        if not entry.get("models") or not isinstance(entry["models"], list):
            raise PermissionsDefinitionError(f"Permission {permission_name} models key should be a list of strings.")
        models: list[str] = entry["models"]
        if entry.get("additional_actions") and not isinstance(entry.get("additional_actions"), str):
            raise PermissionsDefinitionError(
                f"Permission {permission_name}'s additional_actions valus must be a string or absent from the permission entry."
            )
        additional_actions = entry.get("additional_actions")
        if entry.get("constraints") and not isinstance(entry.get("constraints"), list):
            raise PermissionsDefinitionError(
                f"Permission '{permission_name}': 'constraints' must be a list or absent from the permission entry."
            )
        constraints = entry["constraints"]
        return {
            "name": permission_name,
            "groups": permission_groups,
            "app": app_label,
            "actions": actions,
            "models": models,
            "additional_actions": additional_actions,
            "constraints": constraints,
        }

    def load_definition(self) -> tuple[list[str], list[dict[str, Any]]]:
        """Read and validate the YAML file, resolving every reference.

        Returns:
            A tuple of ``(group_names, plan)``, where each plan entry holds the
            permission name, its resolved ContentTypes, actions, constraints and
            group names.

        Raises:
            PermissionsDefinitionError: If the file is missing or invalid.
        """
        document: dict[str, Any] = validate_yaml_file()

        group_names = document.get("groups") or []
        if not isinstance(group_names, list) or not all(isinstance(item, str) for item in group_names):
            raise PermissionsDefinitionError("'groups' must be a list of strings.")

        entries = document.get("permissions") or []
        if not isinstance(entries, list):
            raise PermissionsDefinitionError("'permissions' must be a list.")

        plan = []
        seen = set()
        for entry in entries:
            valid_perm_attrs: dict[str, Any] = self.validate_entry(entry)
            if valid_perm_attrs["name"] in seen:
                raise PermissionsDefinitionError(f"Duplicate permission name '{valid_perm_attrs['name']}'.")
            seen.add(valid_perm_attrs["name"])
            for group_name in valid_perm_attrs["groups"]:
                if group_name not in group_names:
                    raise PermissionsDefinitionError(
                        f"Permission '{valid_perm_attrs['name']}' references group '{group_name}', "
                        "which is not listed under 'groups'."
                    )

            plan.append(
                {
                    "name": valid_perm_attrs["name"],
                    "actions": valid_perm_attrs["actions"],
                    "object_types": resolve_object_types(
                        valid_perm_attrs["app"], valid_perm_attrs["models"], valid_perm_attrs["name"]
                    ),
                    "constraints": normalize_constraints(valid_perm_attrs["constraints"]),
                    "groups": sorted(valid_perm_attrs["groups"]),
                    "additional_actions": valid_perm_attrs["additional_actions"],
                }
            )

        return group_names, plan

    def sync_groups(self, group_names: list[str]) -> dict[str, Group]:
        """Create any group that does not exist yet.

        Args:
            group_names: Group names from the YAML file.

        Returns:
            Mapping of group name to Group instance.
        """
        groups = {}
        for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)
            groups[group_name] = group
            if created:
                self.logger.info("Created group '%s'.", group_name)
        return groups

    def sync_permission(self, entry: dict[str, Any], groups: dict[str, Group]) -> str:
        """Create or update one ObjectPermission.

        Args:
            entry: A validated plan entry from :meth:`load_definition`.
            groups: Mapping of group name to Group instance.

        Returns:
            ``"created"``, ``"updated"`` or ``"unchanged"``.
        """
        permission_name = entry["name"]
        assigned_groups = [groups[group_name] for group_name in entry["groups"]]
        permission = ObjectPermission.objects.filter(name=permission_name).first()

        if permission is None:
            permission = ObjectPermission.objects.create(
                name=permission_name,
                actions=entry["actions"],
                constraints=entry["constraints"],
            )
            permission.object_types.set(entry["object_types"])
            permission.groups.set(assigned_groups)
            self.logger.info("Created permission '%s'.", permission_name, extra={"object": permission})
            return "created"

        changes = []
        if sorted(permission.actions or []) != sorted(entry["actions"]):
            changes.append(f"actions {sorted(permission.actions or [])} -> {sorted(entry['actions'])}")
        if set(permission.object_types.all()) != set(entry["object_types"]):
            changes.append(f"models -> {sorted(str(object_type) for object_type in entry['object_types'])}")
        if normalize_constraints(permission.constraints) != entry["constraints"]:
            changes.append(f"constraints {permission.constraints} -> {entry['constraints']}")
        if sorted(permission.groups.values_list("name", flat=True)) != entry["groups"]:
            changes.append(f"groups -> {entry['groups']}")

        if not changes:
            self.logger.debug("Permission '%s' is already in sync.", permission_name, extra={"object": permission})
            return "unchanged"

        permission.actions = entry["actions"]
        permission.constraints = entry["constraints"]
        permission.validated_save()
        permission.object_types.set(entry["object_types"])
        permission.groups.set(assigned_groups)
        self.logger.info(f"Updated permission '{permission_name}': {'; '.join(changes)}", extra={"object": permission})
        return "updated"

    def run(self, *, dryrun: bool = False) -> str:  # pylint: disable=arguments-differ
        """Reconcile Nautobot with the YAML file.

        Args:
            dryrun: Apply the changes inside a transaction, then roll it back.

        Returns:
            A one-line summary.
        """
        group_names, plan = self.load_definition()
        self.logger.info(
            f"Loaded {len(group_names)} group(s) and {len(plan)} permission(s) from {PERMISSIONS_FILE.name}.",
        )

        counts = {"created": 0, "updated": 0, "unchanged": 0}
        with transaction.atomic():
            groups = self.sync_groups(group_names)
            for entry in plan:
                counts[self.sync_permission(entry, groups)] += 1
            if dryrun:
                transaction.set_rollback(True)

        summary = (
            f"{'Dry run, rolled back: ' if dryrun else ''}"
            f"{counts['created']} created, {counts['updated']} updated, {counts['unchanged']} unchanged."
        )
        self.logger.info(summary)
        return summary


register_jobs(ManagePermissionsFromYAML)
