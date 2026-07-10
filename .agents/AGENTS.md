# PicoLibrary Project Rules

## Creating New Python Classes
- **Skill Usage**: Always consult and follow the `class-creator` skill (located in `.agents/skills/class-creator`) when generating new Python class files.
- **Header Standard**: Prepend every class file with a triple-quoted block containing the filename, description, and author (`Arijit Sengupta`).
- **Logging Standard**: Use the custom `Log` module (`from Log import *`) and use `Log.i()` instead of raw `print` statements.
- **Testing Standard**: Add a runnable `if __name__ == "__main__":` test block at the bottom of class files to perform self-contained verification.
