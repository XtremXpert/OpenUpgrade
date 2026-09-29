# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
Convert the custom ir.model.access and ir.rule records of Odoo 19 into
ir.access records (loaded by the post- and end-migration scripts of base).

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
  carrying the rule's domain. This runs in post-migration for the
  permissions of base and again in end-migration for the other modules;
- a standard ACL or rule deactivated in Odoo 19 deactivates the ir.access
  with the same xmlid.

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


def _rows(cr):
    return [
        dict(zip([col.name for col in cr.description], row, strict=True))
        for row in cr.fetchall()
    ]


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
    acls = _rows(cr)
    cr.execute(
        f"""
        SELECT id, name, active, model_id, domain_force,
               perm_read, perm_write, perm_create, perm_unlink
        FROM {_legacy("ir_rule")}
        """
    )
    rules = _rows(cr)
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


class Converter:
    def __init__(self, env):
        self.env = env
        self.cr = env.cr
        self.xmlids, self.acls, self.rules = _load_legacy(env.cr)
        self.IrAccess = env["ir.access"].sudo().with_context(active_test=False)
        self.everyone = env.ref("base.group_everyone")
        self.cr.execute("SELECT id FROM ir_model")
        self.model_ids = {row[0] for row in self.cr.fetchall()}
        self.cr.execute("SELECT id FROM res_groups")
        self.group_ids = {row[0] for row in self.cr.fetchall()}
        self._closures = {}
        self.group_rules = {}
        self.warnings = []
        for rule in self.rules:
            if rule["active"] and rule["groups"]:
                self.group_rules.setdefault(rule["model_id"], []).append(rule)
        self.created = _legacy("ir_access_created")
        if not openupgrade.table_exists(self.cr, self.created):
            self.cr.execute(f"CREATE TABLE {self.created} (id integer, origin text)")

    def is_custom(self, model, res_id):
        module = self.xmlids.get((model, res_id), (None, None))[0]
        return module is None or module in CUSTOM_MODULES

    def closure(self, group_id):
        """The groups every user of group_id belongs to (group and implied)."""
        if group_id not in self._closures:
            group = self.env["res.groups"].sudo().browse(group_id)
            self._closures[group_id] = set(group.all_implied_ids.ids) | {group_id}
        return self._closures[group_id]

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
        """Create the ir.access with SQL: the model may belong to a module
        that is not loaded yet, so the domain is validated in end-migration."""
        self.cr.execute(
            """
            INSERT INTO ir_access
                (name, active, model_id, group_id, operation, domain, note,
                 create_uid, create_date, write_uid, write_date)
            VALUES (%s, TRUE, %s, %s, %s, %s, %s, 1, now(), 1, now())
            RETURNING id
            """,
            (
                values["name"],
                values["model_id"],
                values.get("group_id") or None,
                values["operation"],
                values.get("domain") or None,
                f"<p>Converted by OpenUpgrade from {origin}.</p>",
            ),
        )
        access_id = self.cr.fetchone()[0]
        self.cr.execute(
            f"INSERT INTO {self.created} (id, origin) VALUES (%s, %s)",
            (access_id, origin),
        )
        return access_id

    def convert_custom_acls(self):
        for acl in self.acls:
            if not self.is_custom("ir.model.access", acl["id"]):
                continue
            origin = f"ir.model.access '{acl['name']}'"
            if acl["model_id"] not in self.model_ids:
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
                        "domain": domain,
                    },
                    origin,
                )

    def convert_custom_global_rules(self):
        for rule in self.rules:
            if rule["groups"] or not self.is_custom("ir.rule", rule["id"]):
                continue
            origin = f"ir.rule '{rule['name']}'"
            if rule["model_id"] not in self.model_ids:
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
                    "domain": rule["domain"],
                },
                origin,
            )

    def standard_permissions(self):
        """The active permissions defined by a module (with a real xmlid)."""
        self.cr.execute(
            """
            SELECT access.id
            FROM ir_access access
            JOIN ir_model_data data
                ON data.model = 'ir.access' AND data.res_id = access.id
            WHERE access.active AND access.group_id IS NOT NULL
                AND data.module NOT IN %s
            """,
            (CUSTOM_MODULES,),
        )
        return self.IrAccess.browse([row[0] for row in self.cr.fetchall()])

    def apply_custom_group_rules(self, final):
        """Restrict the standard permissions with the custom group rules."""
        permissions = self.standard_permissions()
        by_permission = {}
        for rule in self.rules:
            if not rule["groups"] or not self.is_custom("ir.rule", rule["id"]):
                continue
            origin = f"ir.rule '{rule['name']}'"
            if rule["model_id"] not in self.model_ids:
                if final:
                    self.warnings.append(f"{origin}: model does not exist anymore")
                continue
            if not rule["active"] or not rule["domain"]:
                continue
            applied = False
            for permission in permissions:
                if permission.model_id.id != rule["model_id"]:
                    continue
                if not rule["groups"] & self.closure(permission.group_id.id):
                    continue
                by_permission.setdefault(permission, []).append(rule)
                applied = True
            if final and not applied:
                self.warnings.append(
                    f"{origin}: no standard permission of model "
                    f"{permission_model(self.env, rule['model_id'])} is granted to "
                    "its groups, so the rule could not be converted; review the "
                    "accesses of the model"
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

    def validate_created(self):
        """Once every model is loaded, deactivate the converted accesses whose
        domain is not valid anymore."""
        self.cr.execute(f"SELECT id, origin FROM {self.created}")
        for access_id, origin in self.cr.fetchall():
            access = self.IrAccess.browse(access_id).exists()
            if not access or not access.active or not access.domain:
                continue
            if access.model_id.model not in self.env:
                continue
            try:
                with self.cr.savepoint():
                    access._check_domain()
            except ValidationError as error:
                access.active = False
                self.warnings.append(
                    f"{origin}: deactivated, its domain is not valid anymore "
                    f"({error.args[0]})"
                )

    def run(self, final=False):
        if not final:
            self.convert_custom_acls()
            self.convert_custom_global_rules()
        self.apply_custom_group_rules(final)
        self.deactivate_customized_standard_records()
        if final:
            self.validate_created()
        for warning in self.warnings:
            _logger.warning("Access conversion: %s", warning)
        self.IrAccess._clear_caches()


def permission_model(env, model_id):
    env.cr.execute("SELECT model FROM ir_model WHERE id = %s", (model_id,))
    row = env.cr.fetchone()
    return row and row[0]


def convert(env, final=False):
    if openupgrade.table_exists(env.cr, _legacy("access_xmlids")):
        Converter(env).run(final=final)
