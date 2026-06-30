# nomens

A lightweight utility for representing "namespaces" in Python.
By inheriting from the `namespace` class, you can easily create classes
that are non-instantiable, support attribute freezing, and can hide
private attributes from normal access.

## Features

- **Prevents instantiation**: Calling a class that inherits from
  `namespace` with `()` raises a `TypeError`, so instances cannot be
  created. It is intended to be used purely as a "namespace" for
  grouping constants and functions.
- **Attribute freezing (frozen)**: By default, attributes cannot be
  added, edited, or deleted after the class is defined. This prevents
  accidental modification of the namespace's contents.
- **Partial unfreezing**: Attributes specified in `unfrozen_attrs` can
  still be modified even while frozen.
- **Private attributes**: Attributes specified in `priv_attrs` are
  hidden from normal attribute access (an `AttributeError` is raised
  instead).
- **Temporary unfreezing**: Using the `with namespace.unfrozen():`
  context manager, you can make attributes editable only within a
  specific scope.
- **Duplicate definition detection**: Defining an attribute with the
  same name twice within the class body raises a `ValueError`.

## Basic usage

```python
from nomens import namespace

class Config(namespace):
    DEBUG = False
    VERSION = "1.0.0"

# Normal reads are fine
print(Config.VERSION)  # "1.0.0"

# Since it's frozen, modification raises an error
Config.DEBUG = True  # AttributeError: Cannot assign to DEBUG in namespace Config

# Instantiation also raises an error
Config()  # TypeError: namespace Config is not intended to be instantiated.
```

## Class arguments

When inheriting from `namespace`, you can customize behavior with the
following class arguments:

```python
class Config(namespace, frozen=True, unfrozen_attrs=["CACHE"], priv_attrs=["_secret"]):
    DEBUG = False
    CACHE = {}
    _secret = "hidden"
```

| Argument | Type | Default | Description |
|---|---|---|---|
| `frozen` | `bool` | `True` | Whether to prohibit adding, editing, and deleting attributes. |
| `unfrozen_attrs` | `Sequence[str] \| None` | `None` | A list of attribute names that remain editable even when `frozen=True`. |
| `priv_attrs` | `Sequence[str] \| None` | `None` | A list of attribute names to hide from normal attribute access. |

> **Note**: `namespace` must be inherited from directly (multi-level
> inheritance is not allowed). Attempting multi-level inheritance
> raises a `TypeError`.

## Temporarily unfreezing

By combining the `unfrozen()` class method with a `with` statement, you
can allow attribute editing only within a specific scope. Upon exiting
the `with` block, the original frozen state is automatically restored.

```python
class Config(namespace):
    COUNT = 0

# Temporarily unfreeze all attributes
with Config.unfrozen():
    Config.COUNT += 1

# Temporarily unfreeze only the specified attribute
with Config.unfrozen("COUNT"):
    Config.COUNT += 1
```

## Private attributes

Attributes specified in `priv_attrs` raise an `AttributeError` on
normal access.

```python
class Config(namespace, priv_attrs=["_secret"]):
    _secret = "hidden"

Config._secret  # AttributeError: Config has no public attribute _secret.
```

## Class methods

| Method | Description |
|---|---|
| `is_frozen()` | Returns whether the namespace is currently frozen, as a `bool`. |
| `unfrozen_attrs()` | Returns the list of attribute names that remain operable while frozen, as a `list[str]`. |
| `private_attrs()` | Returns the list of attribute names hidden as private attributes. |
| `unfrozen(*args)` | A context manager for temporarily unfreezing. |

## Intended use cases

- Grouping configuration values or constants while preventing them from
  being accidentally modified
- Grouping global utility functions in a form that doesn't require
  instantiation
- Allowing only certain values to be updated at runtime while keeping
  everything else immutable
