SYSTEM_ROLES = ("candidate", "company", "admin")

ROLE_PERMISSIONS = {
    "candidate": [
        "profile:read",
        "profile:write",
        "resume:upload",
        "resume:read",
        "job:list",
        "job:save",
        "application:create",
        "application:read_own",
        "ai:analyze",
        "notification:read_own",
    ],
    "company": [
        "company:read",
        "company:write",
        "job:create",
        "job:read_own",
        "job:update_own",
        "job:delete_own",
        "application:read_company",
        "application:update_company",
        "candidate:search_company",
        "ai:rank_candidates",
        "notification:read_own",
    ],
    "admin": [
        "admin:read",
        "admin:write",
        "user:manage",
        "company:manage",
        "taxonomy:manage",
        "audit:read",
        "metrics:read",
    ],
}
