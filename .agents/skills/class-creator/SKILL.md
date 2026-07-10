---
name: class-creator
description: Use this skill whenever creating or adding a new Python class to the PicoLibrary project. It ensures that the class follows the project's formatting standards, includes the standard file header, uses proper logging, and includes self-contained test execution blocks.
---

# Class Creator Skill

This skill enforces standards for adding new Python classes to the PicoLibrary repository. All new class files must strictly follow these header and testing guidelines.

## 1. File Header Template

Every new Python file containing a class MUST begin with a triple-quoted comment block containing the filename, a description of the module/classes, and the author name. 

Use the following format exactly:

```python
"""
# <Filename>.py
# <A concise description of the file, its purpose, and the classes it implements>
# Author: Arijit Sengupta
"""
```

**Example:**
```python
"""
# TemperatureSensor.py
# Implementation of a temperature sensor reading from an analog pin
# Author: Arijit Sengupta
"""
```

## 2. Coding Standards

- **Logging**: Use the project's custom `Log` utility. Import it as `from Log import *` and log events using `Log.i("Message")`. Avoid using raw `print()` statements for standard operations.
- **Imports**: Place standard libraries at the top of the file, followed by project-specific imports. Use lazy imports whenever possible, so that the import is only done when a class is instantiated or a method is called. This ensures that the this file can be imported even if the required libraries are not installed on the target device, as long as the function that requires the library is not called.
- **Docstrings**: Include clear, concise docstrings for the class and all public methods. Use markdown to format the docstrings, including bold, italics, etc. Include examples of how to use the class and its methods. Include a section on Parameters - use the following format:

```
Parameters:
----------
param1 : type
    Description of param1
param2 : type, optional
    Description of param2 (default: default_value)
```

Include a section on Examples - use the following format:

```
Examples:
---------
1. Example 1
2. Example 2
```

## 3. Test Rules

Every new class file must be self-contained and runnable for verification purposes.

- Place a test execution block at the bottom of the file:
  ```python
  if __name__ == "__main__":
      # Test code here
  ```
- Within the test block:
  1. Instantiate the class with test pins or parameters.
  2. Invoke major methods and verify their execution.
  3. Use assertions or log statements to confirm correct behavior.
  4. Ensure any imported hardware modules (like `machine` or `time`) are used safely or mocked if testing in a non-hardware environment.
  5. Conclude with a log statement confirming test completion: `Log.i("Testing complete - ...")`.

**Example Test Block:**
```python
if __name__ == "__main__":
    # Create the sensor and test reading values
    sensor = TemperatureSensor(pin=26, name="Test Sensor")
    val = sensor.readTemp()
    Log.i(f"Read temperature: {val}")
    
    Log.i("Testing complete - all checks passed")
```
