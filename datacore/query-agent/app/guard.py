"""SQL validation — read-only enforcement."""

import re
import sqlparse

FORBIDDEN = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "GRANT", "REVOKE", "EXECUTE", "CALL", "MERGE", "COPY",
    "VACUUM", "ANALYZE", "REINDEX", "SET", "PREPARE", "EXECUTE",
    "DEALLOCATE", "LISTEN", "NOTIFY",
}

DANGEROUS = [
    (r"pg_sleep", "timeout attack"),
    (r"pg_read_file", "file read"),
    (r"pg_read_binary_file", "binary read"),
    (r"current_setting", "config leak"),
    (r"COPY\s+.*TO\s+", "file write"),
    (r"COPY\s+.*FROM\s+", "file read"),
    (r"\\\';", "SQL injection"),
]


def validate(sql: str) -> tuple[bool, str]:
    """Только SELECT. Возвращает (ok, cleaned_sql|error)."""
    s = sql.strip().rstrip(";").strip()
    if not s:
        return False, "Empty query"

    for pat, reason in DANGEROUS:
        if re.search(pat, s, re.IGNORECASE):
            return False, f"Rejected: {reason}"

    parsed = sqlparse.parse(s)
    if not parsed:
        return False, "Unparseable SQL"

    for stmt in parsed:
        t = stmt.get_type().upper()
        if t not in {"SELECT", "WITH", "EXPLAIN", "VALUES"}:
            return False, f"Only SELECT allowed, got {t}"

        raw = stmt.value.upper()
        for f in FORBIDDEN:
            if re.search(rf"\b{f}\b", raw):
                return False, f"Rejected: {f} not allowed"

    return True, s


def mask(sql: str) -> str:
    return re.sub(r"(password|secret|token|key|auth)\s*=\s*['\"][^'\"]+['\"]",
                  r"\1=***", sql, flags=re.IGNORECASE)