# Code Snippet Example

## Python Example1

```python
# Print Hello World
print("Hello, World!")
```

## Python Example2

```python
# Add two numbers
"""
A command-line program that accepts two numbers and returns their sum.
"""

import sys
import argparse


def add_numbers(num1, num2):
    """Add two numbers and return the result."""
    return num1 + num2


def main():
    """Main function to handle command-line arguments and execute the program."""
    parser = argparse.ArgumentParser(
        description="Add two numbers together",
        usage="%(prog)s num1 num2"
    )
    parser.add_argument("num1", type=float, help="First number")
    parser.add_argument("num2", type=float, help="Second number")
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 1
    
    try:
        args = parser.parse_args()
        result = add_numbers(args.num1, args.num2)
        print(f"{args.num1} + {args.num2} = {result}")
        return 0
    except ValueError as e:
        print(f"Error: Invalid input. Please provide valid numbers.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

## JavaScript Example

```javascript
// Print current time
console.log(new Date().toISOString());
```

## Bash Example

```bash
# List files in current directory
ls -la
```
