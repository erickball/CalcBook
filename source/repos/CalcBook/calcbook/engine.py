"""Execution engine for CalcBook. Evaluates Python expressions in a shared namespace."""

import math


class ExecutionEngine:
    """Evaluates cells/expressions top-to-bottom in a shared namespace."""

    def __init__(self):
        self.namespace = {}
        self._build_default_namespace()
        self.blocks = []  # ordered list of blocks to evaluate

    def _build_default_namespace(self):
        """Populate namespace with math functions and common imports."""
        self.namespace = {"__builtins__": __builtins__}
        # Add math functions directly
        for name in dir(math):
            if not name.startswith("_"):
                self.namespace[name] = getattr(math, name)
        try:
            import numpy as np
            self.namespace["np"] = np
        except ImportError:
            pass

    def register_block(self, block):
        if block not in self.blocks:
            self.blocks.append(block)

    def unregister_block(self, block):
        if block in self.blocks:
            self.blocks.remove(block)

    def evaluate(self, expression):
        """Evaluate a single expression, returning (result, error)."""
        if not expression or not expression.strip():
            return None, None
        try:
            result = eval(expression, self.namespace)
            return result, None
        except SyntaxError:
            # Try exec for statements (assignments, etc.)
            try:
                exec(expression, self.namespace)
                return None, None
            except Exception as e:
                return None, str(e)
        except Exception as e:
            return None, str(e)

    def run_all(self):
        """Re-execute all blocks top-to-bottom."""
        self._build_default_namespace()
        for block in self.blocks:
            block.execute(self)
