# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
Convert the custom ir.model.access and ir.rule records of Odoo 19 into
ir.access records.

This runs at the end of the migration, once every module has loaded its own
ir.access records, because a custom group rule of Odoo 19 must be applied to
the standard permissions of the group it restricts.

Semantics in Odoo 19:
- access is granted by any ACL of the user's groups (or a global ACL);
- global rules restrict everybody (AND);
- group rules restrict the users of their groups; when several group rules
  apply to a user, the records satisfying any of them are allowed (OR).

Semantics in Odoo 20:
- a permission is an ir.access with a group: the records of its domain are
  allowed to the users of the group; permissions are OR-ed;
- a restriction is an ir.access without group: it applies to everybody and
  restrictions are AND-ed.

Conversion:
- a custom ACL becomes a permission of its group (base.group_everyone for a
  global ACL); the domains of the group rules that apply to every user of the
  group are folded into it (OR), per operation;
- a custom global rule becomes a restriction;
- a custom group rule restricts the standard permissions of the groups it
  applies to: the standard permission is deactivated and replaced by a copy
  carrying the rule's domain.

Like Odoo's own conversion of its standard records, this cannot express a
group rule for users who get their access through another group: such cases
are logged for review.
"""

import logging

from openupgradelib import openupgrade

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

CUSTOM_MODULES = ("__export__", "__custom__", "__import__", "studio_customization")
TRUE_DOMAINS = ("[]", "[(1, '=', 1)]", "[(1,'=',1)]", '[(1, "=", 1)]')


def _legacy(name):
    return openupgrade.get_legacy_name(name)


def _clean_domain(domain):
    domain = (domain or "").strip()
    return "" if domain in TRUE_DOMAINS else domain


def _combine(operator, domains):
    """Combine domain expressions (strings) with a prefix operator."""
    domains = [domain for domain in domains if domain]
    if not domains:
        return ""
    if len(domains) == 1:
        return domains[0]
    joined = " + ".join(f"({domain})" for domain in domains)
    return f"[{operator!r}] * {len(domains) - 1} + {joined}"


def _operations(row):
    return "".join(
        letter
        for letter, granted in zip(
            "crud",
            (
                row["perm_create"],
                row["perm_read"],
                row["perm_write"],
                row["perm_unlink"],
            ),
            strict=True,
        )
        if granted
    )


def _load_legacy(cr):
    cr.execute(f"SELECT model, res_id, module, name FROM {_legacy('access_xmlids')}")
    xmlids = {}
    for model, res_id, module, name in cr.fetchall():
        xmlids.setdefault((model, res_id), (module, name))
    cr.execute(
        f"""
        SELECT id, name, active, model_id, group_id,
               perm_read, perm_write, perm_create, perm_unlink
        FROM {_legacy("ir_model_access")}
        """
    )
    acls = [
        dict(zip([col.name for col in cr.description], row, strict=True))
        for row in cr.fetchall()
    ]
    cr.execute(
        f"""
        SELECT id, name, active, model_id, domain_force,
               perm_read, perm_write, perm_create, perm_unlink
        FROM {_legacy("ir_rule")}
        """
    )
    rules = [
        dict(zip([col.name for col in cr.description], row, strict=True))
        for row in cr.fetchall()
    ]
    rule_groups = {}
    if openupgrade.table_exists(cr, _legacy("rule_group_rel")):
        cr.execute(f"SELECT rule_group_id, group_id FROM {_legacy('rule_group_rel')}")
        for rule_id, group_id in cr.fetchall():
            rule_groups.setdefault(rule_id, set()).add(group_id)
    for rule in rules:
        rule["groups"] = rule_groups.get(rule["id"], set())
        rule["domain"] = _clean_domain(rule["domain_force"])
        rule["operations"] = _operations(rule)
    for acl in acls:
        acl["operations"] = _operations(acl)
    return xmlids, acls, rules


class _Converter:
    def __init__(self, env):
        self.env = env
        self.xmlids, self.acls, self.rules = _load_legacy(env.cr)
        self.IrAccess = env["ir.access"].sudo().with_context(active_test=False)
        self.everyone = env.ref("base.group_everyone")
        self.model_names = {
            model.id: model.model for model in env["ir.model"].sudo().search([])
        }
        self.group_ids = set(env["res.groups"].sudo().search([]).ids)
        self._closures = {}
        self.group_rules = {}
        self.warnings = []
        for rule in self.rules:
            if rule["active"] and rule["groups"]:
                self.group_rules.setdefault(rule["model_id"], []).append(rule)

    def is_custom(self, model, res_id):
        module = self.xmlids.get((model, res_id), (None, None))[0]
        return module is None or module in CUSTOM_MODULES

    def closure(self, group_id):
        """The groups every user of group_id belongs to (group and implied)."""
        if group_id not in self._closures:
            group = self.env["res.groups"].sudo().browse(group_id)
            self._closures[group_id] = set(group.all_implied_ids.ids) | {group_id}
        return self._closures[group_id]

    def model_name(self, model_id):
        name = self.model_names.get(model_id)
        return name if name in self.env else None

    def folded_domain(self, model_id, group_id, operation):
        """OR of the group rules applying to every user of the group."""
        closure = self.closure(group_id)
        return _combine(
            "|",
            [
                rule["domain"]
                for rule in self.group_rules.get(model_id, [])
                if operation in rule["operations"] and rule["groups"] & closure
            ],
        )

    def create(self, values, origin):
        values = dict(values, note=f"Converted by OpenUpgrade from {origin}.")
        try:
            with self.env.cr.savepoint():
                return self.IrAccess.create(values)
        except ValidationError as error:
            self.warnings.append(
                f"{origin}: created inactive, its domain is not valid anymore "
                f"({error.args[0]})"
            )
            return self.IrAccess.create(dict(values, active=False))

    def convert_custom_acls(self):
        for acl in self.acls:
            if not self.is_custom("ir.model.access", acl["id"]):
                continue
            origin = f"ir.model.access '{acl['name']}'"
            model_name = self.model_name(acl["model_id"])
            if not model_name:
                self.warnings.append(f"{origin}: model does not exist anymore")
                continue
            if not acl["active"]:
                _logger.info("%s: inactive, not converted", origin)
                continue
            if acl["group_id"] and acl["group_id"] not in self.group_ids:
                self.warnings.append(f"{origin}: group does not exist anymore")
                continue
            group_id = acl["group_id"] or self.everyone.id
            by_domain = {}
            for operation in acl["operations"]:
                domain = self.folded_domain(acl["model_id"], group_id, operation)
                by_domain[domain] = by_domain.get(domain, "") + operation
            for domain, operations in by_domain.items():
                self.create(
                    {
                        "name": acl["name"],
                        "model_id": acl["model_id"],
                        "group_id": group_id,
                        "operation": operations,
                        "domain": domain or False,
                    },
                    origin,
                )

    def convert_custom_global_rules(self):
        for rule in self.rules:
            if rule["groups"] or not self.is_custom("ir.rule", rule["id"]):
                continue
            origin = f"ir.rule '{rule['name']}'"
            if not self.model_name(rule["model_id"]):
                self.warnings.append(f"{origin}: model does not exist anymore")
                continue
            if not rule["active"] or not rule["operations"]:
                _logger.info("%s: inactive, not converted", origin)
                continue
            self.create(
                {
                    "name": rule["name"],
                    "model_id": rule["model_id"],
                    "group_id": False,
                    "operation": rule["operations"],
                    "domain": rule["domain"] or False,
                },
                origin,
            )

    def apply_custom_group_rules(self, standard_permissions):
        """Restrict the standard permissions with the custom group rules."""
        by_permission = {}
        for rule in self.rules:
            if not rule["groups"] or not self.is_custom("ir.rule", rule["id"]):
                continue
            origin = f"ir.rule '{rule['name']}'"
            if not self.model_name(rule["model_id"]):
                self.warnings.append(f"{origin}: model does not exist anymore")
                continue
            if not rule["active"] or not rule["domain"]:
                _logger.info("%s: inactive or without domain, not converted", origin)
                continue
            applied = False
            for permission in standard_permissions:
                if permission.model_id.id != rule["model_id"]:
                    continue
                if not rule["groups"] & self.closure(permission.group_id.id):
                    continue
                by_permission.setdefault(permission, []).append(rule)
                applied = True
            if not applied:
                self.warnings.append(
                    f"{origin}: no standard permission of model "
                    f"{self.model_name(rule['model_id'])} is granted to its groups, "
                    "so the rule could not be converted; review the accesses of "
                    "the model"
                )
        for permission, rules in by_permission.items():
            base_domain = _clean_domain(permission.domain)
            by_domain = {}
            for operation in permission.operation:
                applying = [
                    rule["domain"] for rule in rules if operation in rule["operations"]
                ]
                domain = (
                    _combine("|", [base_domain] + applying) if applying else base_domain
                )
                by_domain[domain] = by_domain.get(domain, "") + operation
            if list(by_domain) == [base_domain]:
                continue
            names = ", ".join(f"'{rule['name']}'" for rule in rules)
            for domain, operations in by_domain.items():
                permission.copy(
                    {
                        "operation": operations,
                        "domain": domain or False,
                        "active": True,
                        "note": f"Copy of '{permission.name}' restricted by "
                        f"OpenUpgrade with ir.rule {names}.",
                    }
                )
            permission.active = False
            _logger.info(
                "Standard permission '%s' (%s) replaced by copies restricted with %s",
                permission.name,
                permission.model_id.model,
                names,
            )

    def deactivate_customized_standard_records(self):
        """A standard ACL or rule that was deactivated in Odoo 19 keeps the
        same xmlid as an ir.access record in Odoo 20: deactivate that one."""
        inactive = {
            ("ir.model.access", acl["id"]) for acl in self.acls if not acl["active"]
        } | {("ir.rule", rule["id"]) for rule in self.rules if not rule["active"]}
        for key in inactive:
            module, name = self.xmlids.get(key, (None, None))
            if not module or module in CUSTOM_MODULES:
                continue
            access = self.env.ref(f"{module}.{name}", raise_if_not_found=False)
            if access and access._name == "ir.access" and access.active:
                access.active = False
                _logger.info("%s.%s deactivated as it was in Odoo 19", module, name)

    def run(self):
        standard_permissions = self.IrAccess.search(
            [("group_id", "!=", False), ("active", "=", True)]
        )
        self.convert_custom_acls()
        self.convert_custom_global_rules()
        self.apply_custom_group_rules(standard_permissions)
        self.deactivate_customized_standard_records()
        for warning in self.warnings:
            _logger.warning("Access conversion: %s", warning)
        self.IrAccess._clear_caches()


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.table_exists(env.cr, _legacy("access_xmlids")):
        _Converter(env).run()
    openupgrade.disable_invalid_filters(env)
