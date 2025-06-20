import sys

class Output:
    def error(self, message: str):
        raise Exception(message)  # or a custom exception type

    def warning(self, message: str):
        print(f"Warning: {message}", file=sys.stderr)

    def fatal(self, message: str, *args):
        raise SystemExit(f"Fatal error: {message}")
    
    def message(self, mes: str):
        print(f"{message}")
