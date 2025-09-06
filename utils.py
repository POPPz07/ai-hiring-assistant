import re
from lark import Lark, Transformer, v_args

# A simple name validator
def is_valid_name(name: str) -> bool:
    """
    Validates if the name has at least two words and contains only letters and spaces.
    A very basic check.
    """
    return len(name.split()) >= 2 and all(char.isalpha() or char.isspace() for char in name)

# --- More advanced email validation using Lark ---
# This is much more robust than a simple regex.
email_grammar = r"""
    ?start: email

    ?email: local "@" domain

    local: atom ("." atom)*
    domain: atom ("." atom)*

    atom: CNAME

    %import common.CNAME
    %import common.WS
    %ignore WS
"""

class TreeToEmail(Transformer):
    def email(self, parts):
        return "".join(parts)
    def local(self, parts):
        return ".".join(parts)
    def domain(self, parts):
        return ".".join(parts)
    @v_args(inline=True)
    def atom(self, part):
        return str(part)

email_parser = Lark(email_grammar)

def is_valid_email(email: str) -> bool:
    """Validates email format using a grammar parser for robustness."""
    try:
        email_parser.parse(email)
        return True
    except Exception:
        return False

# Simple phone number validation (adjust regex for different country codes if needed)
def is_valid_phone(phone: str) -> bool:
    """Validates a 10-digit phone number."""
    # This regex matches a 10-digit number, optionally with spaces, dashes, or parentheses.
    pattern = re.compile(r"^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$")
    return pattern.match(phone) is not None

def is_valid_experience(experience: str) -> bool:
    """Validates that experience is a number between 0 and 60."""
    try:
        exp = int(experience)
        return 0 <= exp <= 60
    except ValueError:
        return False